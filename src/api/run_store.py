"""In-memory run store for tracking prospecting runs.

In production, this would be backed by a database. For now, we keep
runs in memory with thread-safe access.
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.api.models import RunStatus, RunSummary, RunDetail, NodeProgress
from src.graph.state import ProspectingState


class RunStore:
    """Thread-safe in-memory store for prospecting runs."""

    def __init__(self):
        self._runs: dict[str, dict] = {}
        self._lock = threading.Lock()
        # SSE subscribers: run_id -> list of asyncio.Queue
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def create_run(
        self,
        client_name: str,
        past_sales_history: str,
        base_research_prompt: str,
        project_id: Optional[str] = None,
    ) -> str:
        """Create a new run entry and return its ID."""
        run_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        with self._lock:
            self._runs[run_id] = {
                "run_id": run_id,
                "client_name": client_name,
                "past_sales_history": past_sales_history,
                "base_research_prompt": base_research_prompt,
                "status": RunStatus.PENDING,
                "current_step": "initialized",
                "created_at": now,
                "completed_at": None,
                "plays_count": 0,
                "error": None,
                "state": None,  # Will hold the final ProspectingState
                "project_id": project_id,
            }
        return run_id

    def get_run(self, run_id: str) -> Optional[dict]:
        with self._lock:
            return self._runs.get(run_id)

    def list_runs(self) -> list[RunSummary]:
        with self._lock:
            runs = sorted(
                self._runs.values(),
                key=lambda r: r["created_at"],
                reverse=True,
            )
            return [
                RunSummary(
                    run_id=r["run_id"],
                    client_name=r["client_name"],
                    status=r["status"],
                    current_step=r["current_step"],
                    created_at=r["created_at"],
                    completed_at=r["completed_at"],
                    plays_count=r["plays_count"],
                    error=r["error"],
                    project_id=r.get("project_id"),
                )
                for r in runs
            ]

    def update_step(self, run_id: str, step: str, status: RunStatus = RunStatus.RUNNING):
        with self._lock:
            if run_id in self._runs:
                self._runs[run_id]["current_step"] = step
                self._runs[run_id]["status"] = status

    def complete_run(self, run_id: str, state: ProspectingState):
        with self._lock:
            if run_id in self._runs:
                self._runs[run_id]["status"] = RunStatus.COMPLETED
                self._runs[run_id]["current_step"] = "complete"
                self._runs[run_id]["completed_at"] = datetime.now(timezone.utc)
                self._runs[run_id]["plays_count"] = len(state.refined_plays) if state.refined_plays else 0
                self._runs[run_id]["state"] = state

    def fail_run(self, run_id: str, error: str):
        with self._lock:
            if run_id in self._runs:
                self._runs[run_id]["status"] = RunStatus.FAILED
                self._runs[run_id]["completed_at"] = datetime.now(timezone.utc)
                self._runs[run_id]["error"] = error

    def get_detail(self, run_id: str) -> Optional[RunDetail]:
        with self._lock:
            r = self._runs.get(run_id)
            if not r:
                return None
            state: Optional[ProspectingState] = r.get("state")
            return RunDetail(
                run_id=r["run_id"],
                client_name=r["client_name"],
                status=r["status"],
                current_step=r["current_step"],
                created_at=r["created_at"],
                completed_at=r["completed_at"],
                plays_count=r["plays_count"],
                error=r["error"],
                project_id=r.get("project_id"),
                deep_research_report=state.deep_research_report if state else "",
                client_vertical=state.client_vertical if state else "",
                client_domain=state.client_domain if state else "",
                digital_maturity_summary=state.digital_maturity_summary if state else "",
                competitor_proofs=state.competitor_proofs if state else [],
                refined_plays=state.refined_plays if state else [],
                one_pagers=state.one_pagers if state else {},
                strategic_plan=state.strategic_plan if state else "",
                errors=state.errors if state else [],
            )

    # --- SSE subscriber management ---

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
