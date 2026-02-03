"""FastAPI application for the Deep Prospecting Engine."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.api.models import (
    ProspectRequest,
    RunSummary,
    RunDetail,
    RunStatus,
    NodeProgress,
    HealthResponse,
)
from src.api.run_store import run_store
from src.graph.state import ProspectingState
from src.graph.workflow import build_workflow

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup/shutdown."""
    logger.info("🜆 Deep Prospecting Engine API starting up")
    yield
    logger.info("🜆 Deep Prospecting Engine API shutting down")


app = FastAPI(
    title="Deep Prospecting Engine",
    description="AI-powered sales intelligence pipeline by Pellera",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pipeline runner (background task) ---

PIPELINE_NODES = [
    "input_processor",
    "deep_research",
    "context_merger",
    "competitor_scout",
    "divergent_ideation",
    "convergent_refinement",
    "asset_generator",
    "knowledge_capture",
]


async def _run_pipeline(run_id: str, client_name: str, past_sales_history: str, base_research_prompt: str):
    """Execute the LangGraph pipeline in a background task with progress events."""
    loop = asyncio.get_event_loop()

    try:
        run_store.update_step(run_id, "building_workflow", RunStatus.RUNNING)

        # Build workflow
        workflow = build_workflow()

        initial_state = ProspectingState(
            client_name=client_name,
            past_sales_history=past_sales_history,
            base_research_prompt=base_research_prompt,
        )

        # Stream through nodes for progress
        current_node_idx = 0

        async def run_with_progress():
            nonlocal current_node_idx
            # Run in thread pool since LangGraph is sync
            def _invoke():
                return workflow.invoke(initial_state)

            # Emit starting event
            for node_name in PIPELINE_NODES:
                await run_store.publish(run_id, NodeProgress(
                    run_id=run_id,
                    node=node_name,
                    status="pending",
                    timestamp=datetime.now(timezone.utc),
                ))

            # We can't easily get per-node callbacks from LangGraph invoke,
            # so we run the whole pipeline and emit a completed event.
            # For real per-node streaming, we'd use workflow.stream().
            run_store.update_step(run_id, "running_pipeline", RunStatus.RUNNING)
            await run_store.publish(run_id, NodeProgress(
                run_id=run_id,
                node="pipeline",
                status="started",
                timestamp=datetime.now(timezone.utc),
            ))

            result = await loop.run_in_executor(None, _invoke)
            return result

        final_state = await run_with_progress()

        # Convert result back to ProspectingState if it's a dict
        if isinstance(final_state, dict):
            state = ProspectingState(**final_state)
        else:
            state = final_state

        run_store.complete_run(run_id, state)

        # Emit completion for all nodes
        for node_name in PIPELINE_NODES:
            await run_store.publish(run_id, NodeProgress(
                run_id=run_id,
                node=node_name,
                status="completed",
                timestamp=datetime.now(timezone.utc),
            ))

        await run_store.publish(run_id, NodeProgress(
            run_id=run_id,
            node="pipeline",
            status="completed",
            timestamp=datetime.now(timezone.utc),
        ))

    except Exception as e:
        logger.exception("Pipeline failed for run %s", run_id)
        run_store.fail_run(run_id, str(e))
        await run_store.publish(run_id, NodeProgress(
            run_id=run_id,
            node="pipeline",
            status="failed",
            timestamp=datetime.now(timezone.utc),
            detail=str(e),
        ))
    finally:
        await run_store.publish_done(run_id)


# --- Endpoints ---

@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.post("/api/prospect", response_model=RunSummary, status_code=202, tags=["prospecting"])
async def start_prospect(request: ProspectRequest, background_tasks: BackgroundTasks):
    """Start a new prospecting run. Returns immediately with run ID."""
    run_id = run_store.create_run(
        client_name=request.client_name,
        past_sales_history=request.past_sales_history,
        base_research_prompt=request.base_research_prompt,
    )

    background_tasks.add_task(
        _run_pipeline,
        run_id=run_id,
        client_name=request.client_name,
        past_sales_history=request.past_sales_history,
        base_research_prompt=request.base_research_prompt,
    )

    run = run_store.list_runs()
    return next(r for r in run if r.run_id == run_id)


@app.get("/api/prospect/{run_id}/status", response_model=RunDetail, tags=["prospecting"])
async def get_run_status(run_id: str):
    """Get full status and results for a prospecting run."""
    detail = run_store.get_detail(run_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return detail


@app.get("/api/prospect/{run_id}/stream", tags=["prospecting"])
async def stream_run_progress(run_id: str):
    """SSE endpoint for real-time node progress updates."""
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        queue = run_store.subscribe(run_id)
        try:
            # If already completed, send final state immediately
            current = run_store.get_run(run_id)
            if current and current["status"] in (RunStatus.COMPLETED, RunStatus.FAILED):
                event = NodeProgress(
                    run_id=run_id,
                    node="pipeline",
                    status="completed" if current["status"] == RunStatus.COMPLETED else "failed",
                    timestamp=datetime.now(timezone.utc),
                )
                yield f"data: {event.model_dump_json()}\n\n"
                return

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=60.0)
                    if event is None:  # Done sentinel
                        yield f"data: {json.dumps({'done': True})}\n\n"
                        break
                    yield f"data: {event.model_dump_json()}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        finally:
            run_store.unsubscribe(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/runs", response_model=list[RunSummary], tags=["prospecting"])
async def list_runs():
    """List all prospecting runs, most recent first."""
    return run_store.list_runs()
