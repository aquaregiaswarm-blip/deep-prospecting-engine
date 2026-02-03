"""Database-backed project store for managing prospecting projects.

Uses SQLAlchemy async sessions for FastAPI endpoints and sync sessions
for operations that may be called from synchronous contexts.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from src.api.models import (
    RunStatus,
    RunSummary,
    ProjectSummary,
    ProjectDetail,
    SavedPlay as SavedPlayModel,
)
from src.db.engine import async_session, SyncSession
from src.db.models import Project as ProjectORM, Run as RunORM, SavedPlay as SavedPlayORM


class ProjectStore:
    """Database-backed store for prospecting projects."""

    # --- Sync methods (backward compatible interface) ---

    def create_project(self, client_name: str, tags: list[str] | None = None, notes: str = "") -> str:
        """Create a new project and return its ID (sync)."""
        project_id = uuid.uuid4().hex[:12]
        with SyncSession() as session:
            row = ProjectORM(
                project_id=project_id,
                client_name=client_name,
                tags=tags or [],
                notes=notes,
            )
            session.add(row)
            session.commit()
        return project_id

    def get_project(self, project_id: str) -> Optional[dict]:
        """Get raw project dict (sync)."""
        with SyncSession() as session:
            row = session.get(ProjectORM, project_id)
            if not row:
                return None
            # Build iteration_ids from related runs
            runs = session.execute(
                select(RunORM.run_id)
                .where(RunORM.project_id == project_id)
                .order_by(RunORM.created_at)
            ).scalars().all()
            return {
                "project_id": row.project_id,
                "client_name": row.client_name,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "tags": row.tags or [],
                "notes": row.notes or "",
                "iteration_ids": list(runs),
            }

    def list_projects(self, run_store) -> list[ProjectSummary]:
        """List all projects as summaries, most recently updated first (sync)."""
        with SyncSession() as session:
            rows = session.execute(
                select(ProjectORM).order_by(ProjectORM.updated_at.desc())
            ).scalars().all()

            summaries = []
            for row in rows:
                # Get latest run status for this project
                latest_run = session.execute(
                    select(RunORM.status)
                    .where(RunORM.project_id == row.project_id)
                    .order_by(RunORM.created_at.desc())
                    .limit(1)
                ).scalar_one_or_none()

                # Count runs and saved plays
                run_count = session.execute(
                    select(RunORM.run_id)
                    .where(RunORM.project_id == row.project_id)
                ).scalars().all()

                saved_plays_count = session.execute(
                    select(SavedPlayORM.play_id)
                    .where(SavedPlayORM.project_id == row.project_id)
                ).scalars().all()

                summaries.append(ProjectSummary(
                    project_id=row.project_id,
                    client_name=row.client_name,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    iteration_count=len(run_count),
                    latest_status=RunStatus(latest_run) if latest_run else None,
                    saved_plays_count=len(saved_plays_count),
                    tags=row.tags or [],
                ))
            return summaries

    def update_project(self, project_id: str, updates: dict) -> bool:
        """Update project fields. Returns False if not found (sync)."""
        with SyncSession() as session:
            row = session.get(ProjectORM, project_id)
            if not row:
                return False
            for key in ("client_name", "notes", "tags"):
                if key in updates and updates[key] is not None:
                    setattr(row, key, updates[key])
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return True

    def delete_project(self, project_id: str) -> bool:
        """Delete a project. Returns False if not found (sync)."""
        with SyncSession() as session:
            row = session.get(ProjectORM, project_id)
            if not row:
                return False
            # Delete saved plays first (FK constraint)
            session.execute(
                delete(SavedPlayORM).where(SavedPlayORM.project_id == project_id)
            )
            session.delete(row)
            session.commit()
            return True

    def add_iteration(self, project_id: str, run_id: str) -> bool:
        """Link a run to a project. The run's project_id is already set at creation.
        Update the project's updated_at timestamp. Returns False if project not found."""
        with SyncSession() as session:
            row = session.get(ProjectORM, project_id)
            if not row:
                return False
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return True

    def save_play(self, project_id: str, iteration_id: str, play_data: dict, notes: str = "") -> Optional[str]:
        """Save a play to the project. Returns play_id or None if project not found (sync)."""
        play_id = uuid.uuid4().hex[:12]
        with SyncSession() as session:
            row = session.get(ProjectORM, project_id)
            if not row:
                return None
            play = SavedPlayORM(
                play_id=play_id,
                project_id=project_id,
                iteration_id=iteration_id,
                play_data=play_data,
                notes=notes,
            )
            session.add(play)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
        return play_id

    def remove_saved_play(self, project_id: str, play_id: str) -> bool:
        """Remove a saved play from a project. Returns False if not found (sync)."""
        with SyncSession() as session:
            play = session.execute(
                select(SavedPlayORM)
                .where(SavedPlayORM.play_id == play_id, SavedPlayORM.project_id == project_id)
            ).scalar_one_or_none()
            if not play:
                return False
            session.delete(play)
            # Update project timestamp
            proj = session.get(ProjectORM, project_id)
            if proj:
                proj.updated_at = datetime.now(timezone.utc)
            session.commit()
            return True

    def get_project_detail(self, project_id: str, run_store) -> Optional[ProjectDetail]:
        """Get full project detail, joining with run data (sync)."""
        with SyncSession() as session:
            row = session.get(ProjectORM, project_id)
            if not row:
                return None

            # Get iterations (runs linked to this project)
            runs = session.execute(
                select(RunORM)
                .where(RunORM.project_id == project_id)
                .order_by(RunORM.created_at)
            ).scalars().all()

            iterations = []
            latest_status = None
            for run in runs:
                iterations.append(RunSummary(
                    run_id=run.run_id,
                    client_name=run.client_name,
                    status=RunStatus(run.status),
                    current_step=run.current_step,
                    created_at=run.created_at,
                    completed_at=run.completed_at,
                    plays_count=run.plays_count or 0,
                    error=run.error,
                    project_id=project_id,
                ))
                latest_status = RunStatus(run.status)

            # Get saved plays
            plays = session.execute(
                select(SavedPlayORM)
                .where(SavedPlayORM.project_id == project_id)
                .order_by(SavedPlayORM.saved_at)
            ).scalars().all()

            saved_plays = [
                SavedPlayModel(
                    play_id=sp.play_id,
                    iteration_id=sp.iteration_id,
                    play_data=sp.play_data,
                    notes=sp.notes or "",
                    saved_at=sp.saved_at,
                )
                for sp in plays
            ]

            return ProjectDetail(
                project_id=row.project_id,
                client_name=row.client_name,
                created_at=row.created_at,
                updated_at=row.updated_at,
                iteration_count=len(iterations),
                latest_status=latest_status,
                saved_plays_count=len(saved_plays),
                tags=row.tags or [],
                notes=row.notes or "",
                iterations=iterations,
                saved_plays=saved_plays,
            )


# Singleton instance
project_store = ProjectStore()
