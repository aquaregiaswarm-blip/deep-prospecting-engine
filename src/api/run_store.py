"""Database-backed run store for tracking prospecting runs.

Uses SQLAlchemy async sessions for FastAPI endpoints and sync sessions
for the LangGraph pipeline (which runs in a thread pool).
SSE subscribers remain in-memory (ephemeral pub/sub).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.api.models import RunStatus, RunSummary, RunDetail, NodeProgress
from src.db.engine import async_session, SyncSession
from src.db.models import Run as RunModel
from src.graph.state import ProspectingState


class RunStore:
    """Database-backed store for prospecting runs.

    Async methods (prefixed with 'a' or used from endpoints) use asyncpg.
    Sync methods (update_step, complete_run, fail_run) use psycopg2 for
    the pipeline thread pool.
    SSE pub/sub stays in-memory.
    """

    def __init__(self):
        # SSE subscribers: run_id -> list of asyncio.Queue (ephemeral, in-memory)
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    # --- Sync methods (called from pipeline thread via run_in_executor) ---

    def create_run(
        self,
        client_name: str,
        past_sales_history: str,
        base_research_prompt: str,
        project_id: Optional[str] = None,
    ) -> str:
        """Create a new run entry and return its ID (sync)."""
        run_id = uuid.uuid4().hex[:12]
        with SyncSession() as session:
            row = RunModel(
                run_id=run_id,
                client_name=client_name,
                past_sales_history=past_sales_history,
                base_research_prompt=base_research_prompt,
                status=RunStatus.PENDING.value,
                current_step="initialized",
                project_id=project_id,
            )
            session.add(row)
            session.commit()
        return run_id

    def get_run(self, run_id: str) -> Optional[dict]:
        """Get raw run dict (sync)."""
        with SyncSession() as session:
            row = session.get(RunModel, run_id)
            if not row:
                return None
            return self._row_to_dict(row)

    def list_runs(self) -> list[RunSummary]:
        """List all runs as summaries, most recent first (sync)."""
        with SyncSession() as session:
            rows = session.execute(
                select(RunModel).order_by(RunModel.created_at.desc())
            ).scalars().all()
            return [self._row_to_summary(r) for r in rows]

    def update_step(self, run_id: str, step: str, status: RunStatus = RunStatus.RUNNING):
        """Update current step and status (sync, called from pipeline thread)."""
        with SyncSession() as session:
            session.execute(
                update(RunModel)
                .where(RunModel.run_id == run_id)
                .values(current_step=step, status=status.value)
            )
            session.commit()

    def complete_run(self, run_id: str, state: ProspectingState):
        """Mark run as completed with all result fields (sync)."""
        with SyncSession() as session:
            session.execute(
                update(RunModel)
                .where(RunModel.run_id == run_id)
                .values(
                    status=RunStatus.COMPLETED.value,
                    current_step="complete",
                    completed_at=datetime.now(timezone.utc),
                    plays_count=len(state.refined_plays) if state.refined_plays else 0,
                    deep_research_report=state.deep_research_report or "",
                    client_vertical=state.client_vertical or "",
                    client_domain=state.client_domain or "",
                    digital_maturity_summary=state.digital_maturity_summary or "",
                    competitor_proofs=state.competitor_proofs if state.competitor_proofs else [],
                    refined_plays=state.refined_plays if state.refined_plays else [],
                    one_pagers=state.one_pagers if state.one_pagers else {},
                    strategic_plan=state.strategic_plan or "",
                    errors=state.errors if state.errors else [],
                )
            )
            session.commit()

    def fail_run(self, run_id: str, error: str):
        """Mark run as failed (sync)."""
        with SyncSession() as session:
            session.execute(
                update(RunModel)
                .where(RunModel.run_id == run_id)
                .values(
                    status=RunStatus.FAILED.value,
                    completed_at=datetime.now(timezone.utc),
                    error=error,
                )
            )
            session.commit()

    def get_detail(self, run_id: str) -> Optional[RunDetail]:
        """Get full run detail (sync)."""
        with SyncSession() as session:
            row = session.get(RunModel, run_id)
            if not row:
                return None
            return self._row_to_detail(row)

    # --- Async methods (called from FastAPI endpoints) ---

    async def alist_runs(self) -> list[RunSummary]:
        """List all runs as summaries, most recent first (async)."""
        async with async_session() as session:
            result = await session.execute(
                select(RunModel).order_by(RunModel.created_at.desc())
            )
            rows = result.scalars().all()
            return [self._row_to_summary(r) for r in rows]

    async def aget_run(self, run_id: str) -> Optional[dict]:
        """Get raw run dict (async)."""
        async with async_session() as session:
            row = await session.get(RunModel, run_id)
            if not row:
                return None
            return self._row_to_dict(row)

    async def aget_detail(self, run_id: str) -> Optional[RunDetail]:
        """Get full run detail (async)."""
        async with async_session() as session:
            row = await session.get(RunModel, run_id)
            if not row:
                return None
            return self._row_to_detail(row)

    # --- Row converters ---

    @staticmethod
    def _row_to_dict(row: RunModel) -> dict:
        return {
            "run_id": row.run_id,
            "client_name": row.client_name,
            "status": RunStatus(row.status),
            "current_step": row.current_step,
            "created_at": row.created_at,
            "completed_at": row.completed_at,
            "plays_count": row.plays_count or 0,
            "error": row.error,
            "project_id": row.project_id,
            "past_sales_history": row.past_sales_history,
            "base_research_prompt": row.base_research_prompt,
        }

    @staticmethod
    def _row_to_summary(row: RunModel) -> RunSummary:
        return RunSummary(
            run_id=row.run_id,
            client_name=row.client_name,
            status=RunStatus(row.status),
            current_step=row.current_step,
            created_at=row.created_at,
            completed_at=row.completed_at,
            plays_count=row.plays_count or 0,
            error=row.error,
            project_id=row.project_id,
        )

    @staticmethod
    def _row_to_detail(row: RunModel) -> RunDetail:
        return RunDetail(
            run_id=row.run_id,
            client_name=row.client_name,
            status=RunStatus(row.status),
            current_step=row.current_step,
            created_at=row.created_at,
            completed_at=row.completed_at,
            plays_count=row.plays_count or 0,
            error=row.error,
            project_id=row.project_id,
            deep_research_report=row.deep_research_report or "",
            client_vertical=row.client_vertical or "",
            client_domain=row.client_domain or "",
            digital_maturity_summary=row.digital_maturity_summary or "",
            competitor_proofs=row.competitor_proofs or [],
            refined_plays=row.refined_plays or [],
            one_pagers=row.one_pagers or {},
            strategic_plan=row.strategic_plan or "",
            errors=row.errors or [],
        )

    # --- SSE subscriber management (in-memory, unchanged) ---

    def subscribe(self, run_id: str) -> asyncio.Queue:
        """Create a new SSE subscriber queue for a run."""
        queue: asyncio.Queue = asyncio.Queue()
        if run_id not in self._subscribers:
            self._subscribers[run_id] = []
        self._subscribers[run_id].append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue):
        """Remove an SSE subscriber."""
        if run_id in self._subscribers:
            try:
                self._subscribers[run_id].remove(queue)
            except ValueError:
                pass

    async def publish(self, run_id: str, event: NodeProgress):
        """Publish a progress event to all subscribers of a run."""
        if run_id in self._subscribers:
            for queue in self._subscribers[run_id]:
                await queue.put(event)

    async def publish_done(self, run_id: str):
        """Signal that the run is complete to all subscribers."""
        if run_id in self._subscribers:
            for queue in self._subscribers[run_id]:
                await queue.put(None)  # sentinel


# Singleton instance
run_store = RunStore()
