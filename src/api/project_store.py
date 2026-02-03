"""In-memory project store for managing prospecting projects.

Similar to RunStore — thread-safe, in-memory. Will be backed by a database later.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.api.models import (
    RunStatus,
    RunSummary,
    ProjectSummary,
    ProjectDetail,
    SavedPlay,
)


class ProjectStore:
    """Thread-safe in-memory store for prospecting projects."""

    def __init__(self):
        self._projects: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create_project(self, client_name: str, tags: list[str] | None = None, notes: str = "") -> str:
        """Create a new project and return its ID."""
        project_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        with self._lock:
            self._projects[project_id] = {
                "project_id": project_id,
                "client_name": client_name,
                "created_at": now,
                "updated_at": now,
                "tags": tags or [],
                "notes": notes,
                "iteration_ids": [],  # ordered list of run_ids
                "saved_plays": [],  # list of SavedPlay dicts
            }
        return project_id

    def get_project(self, project_id: str) -> Optional[dict]:
        """Get raw project dict."""
        with self._lock:
            return self._projects.get(project_id)

    def list_projects(self, run_store) -> list[ProjectSummary]:
        """List all projects as summaries, most recent first."""
        with self._lock:
            projects = sorted(
                self._projects.values(),
                key=lambda p: p["updated_at"],
                reverse=True,
            )
            summaries = []
            for p in projects:
                latest_status = None
                if p["iteration_ids"]:
                    # Get status of the most recent iteration
                    last_run_id = p["iteration_ids"][-1]
                    run = run_store.get_run(last_run_id)
                    if run:
                        latest_status = run["status"]

                summaries.append(ProjectSummary(
                    project_id=p["project_id"],
                    client_name=p["client_name"],
                    created_at=p["created_at"],
                    updated_at=p["updated_at"],
                    iteration_count=len(p["iteration_ids"]),
                    latest_status=latest_status,
                    saved_plays_count=len(p["saved_plays"]),
                    tags=p["tags"],
                ))
            return summaries

    def update_project(self, project_id: str, updates: dict) -> bool:
        """Update project fields. Returns False if not found."""
        with self._lock:
            proj = self._projects.get(project_id)
            if not proj:
                return False
            for key in ("client_name", "notes", "tags"):
                if key in updates and updates[key] is not None:
                    proj[key] = updates[key]
            proj["updated_at"] = datetime.now(timezone.utc)
            return True

    def delete_project(self, project_id: str) -> bool:
        """Delete a project. Returns False if not found."""
        with self._lock:
            if project_id not in self._projects:
                return False
            del self._projects[project_id]
            return True

    def add_iteration(self, project_id: str, run_id: str) -> bool:
        """Add a run ID as an iteration of the project. Returns False if project not found."""
        with self._lock:
            proj = self._projects.get(project_id)
            if not proj:
                return False
            proj["iteration_ids"].append(run_id)
            proj["updated_at"] = datetime.now(timezone.utc)
            return True

    def save_play(self, project_id: str, iteration_id: str, play_data: dict, notes: str = "") -> Optional[str]:
        """Save a play to the project. Returns play_id or None if project not found."""
        play_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        with self._lock:
            proj = self._projects.get(project_id)
            if not proj:
                return None
            proj["saved_plays"].append({
                "play_id": play_id,
                "iteration_id": iteration_id,
                "play_data": play_data,
                "notes": notes,
                "saved_at": now,
            })
            proj["updated_at"] = now
        return play_id

    def remove_saved_play(self, project_id: str, play_id: str) -> bool:
        """Remove a saved play from a project. Returns False if not found."""
        with self._lock:
            proj = self._projects.get(project_id)
            if not proj:
                return False
            original_len = len(proj["saved_plays"])
            proj["saved_plays"] = [p for p in proj["saved_plays"] if p["play_id"] != play_id]
            if len(proj["saved_plays"]) == original_len:
                return False
            proj["updated_at"] = datetime.now(timezone.utc)
            return True

    def get_project_detail(self, project_id: str, run_store) -> Optional[ProjectDetail]:
        """Get full project detail, joining with run_store data."""
        with self._lock:
            proj = self._projects.get(project_id)
            if not proj:
                return None

            # Build iteration summaries from run_store
            iterations: list[RunSummary] = []
            latest_status = None
            for run_id in proj["iteration_ids"]:
                run = run_store.get_run(run_id)
                if run:
                    iterations.append(RunSummary(
                        run_id=run["run_id"],
                        client_name=run["client_name"],
                        status=run["status"],
                        current_step=run["current_step"],
                        created_at=run["created_at"],
                        completed_at=run["completed_at"],
                        plays_count=run["plays_count"],
                        error=run["error"],
                        project_id=project_id,
                    ))
                    latest_status = run["status"]

            saved_plays = [
                SavedPlay(
                    play_id=sp["play_id"],
                    iteration_id=sp["iteration_id"],
                    play_data=sp["play_data"],
                    notes=sp["notes"],
                    saved_at=sp["saved_at"],
                )
                for sp in proj["saved_plays"]
            ]

            return ProjectDetail(
                project_id=proj["project_id"],
                client_name=proj["client_name"],
                created_at=proj["created_at"],
                updated_at=proj["updated_at"],
                iteration_count=len(proj["iteration_ids"]),
                latest_status=latest_status,
                saved_plays_count=len(proj["saved_plays"]),
                tags=proj["tags"],
                notes=proj["notes"],
                iterations=iterations,
                saved_plays=saved_plays,
            )


# Singleton instance
project_store = ProjectStore()
