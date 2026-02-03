"""FastAPI application for the Deep Prospecting Engine."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

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
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectSummary,
    ProjectDetail,
    IterateRequest,
    SavePlayRequest,
    SavedPlay,
)
from src.api.run_store import run_store
from src.api.project_store import project_store
from src.db.engine import init_db
from src.graph.state import ProspectingState
from src.graph.workflow import build_workflow

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup/shutdown."""
    logger.info("🜆 Deep Prospecting Engine API starting up")
    await init_db()
    logger.info("🜆 Database tables initialized")
    yield
    logger.info("🜆 Deep Prospecting Engine API shutting down")


app = FastAPI(
    title="Deep Prospecting Engine",
    description="AI-powered sales intelligence pipeline by Pellera",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server, production, and Vercel previews
_cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

# Add any extra origins from env
_extra_origins = os.environ.get("CORS_EXTRA_ORIGINS", "")
if _extra_origins:
    _cors_origins.extend([o.strip() for o in _extra_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
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


async def _run_pipeline(
    run_id: str,
    client_name: str,
    past_sales_history: str,
    base_research_prompt: str,
    previous_context: Optional[dict] = None,
):
    """Execute the LangGraph pipeline in a background task with progress events.

    Args:
        run_id: The run identifier.
        client_name: Target client name.
        past_sales_history: Prior sales history or relationship context.
        base_research_prompt: Custom research prompt override.
        previous_context: Optional dict with keys 'deep_research_report' and
            'competitor_proofs' from a previous iteration to build upon.
    """
    loop = asyncio.get_event_loop()

    try:
        run_store.update_step(run_id, "building_workflow", RunStatus.RUNNING)

        # Build workflow
        workflow = build_workflow()

        # If building on previous iteration, prepend context
        effective_history = past_sales_history
        effective_prompt = base_research_prompt

        if previous_context:
            prev_report = previous_context.get("deep_research_report", "")
            prev_proofs = previous_context.get("competitor_proofs", [])

            if prev_report:
                effective_history = (
                    f"=== PREVIOUS ITERATION RESEARCH ===\n{prev_report}\n"
                    f"=== END PREVIOUS RESEARCH ===\n\n{effective_history}"
                )

            if prev_proofs:
                proofs_text = "\n".join(
                    f"- {p.get('competitor_name', 'Unknown')}: {p.get('use_case', '')} → {p.get('outcome', '')}"
                    for p in prev_proofs
                )
                effective_history = (
                    f"=== PREVIOUS COMPETITOR PROOFS ===\n{proofs_text}\n"
                    f"=== END COMPETITOR PROOFS ===\n\n{effective_history}"
                )

        initial_state = ProspectingState(
            client_name=client_name,
            past_sales_history=effective_history,
            base_research_prompt=effective_prompt,
        )

        # Stream through nodes for progress
        async def run_with_progress():
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
    """Start a new prospecting run. Returns immediately with run ID.

    If project_id is provided, attaches the run to that project.
    If project_id is not provided, a new project is auto-created.
    """
    project_id = request.project_id

    # Auto-create a project if none specified
    if not project_id:
        project_id = project_store.create_project(
            client_name=request.client_name,
            tags=[],
            notes="Auto-created from /api/prospect",
        )

    # Verify project exists if explicitly provided
    if request.project_id and not project_store.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    run_id = run_store.create_run(
        client_name=request.client_name,
        past_sales_history=request.past_sales_history,
        base_research_prompt=request.base_research_prompt,
        project_id=project_id,
    )

    # Link run to project
    project_store.add_iteration(project_id, run_id)

    background_tasks.add_task(
        _run_pipeline,
        run_id=run_id,
        client_name=request.client_name,
        past_sales_history=request.past_sales_history,
        base_research_prompt=request.base_research_prompt,
    )

    runs = run_store.list_runs()
    return next(r for r in runs if r.run_id == run_id)


@app.get("/api/prospect/{run_id}/status", response_model=RunDetail, tags=["prospecting"])
async def get_run_status(run_id: str):
    """Get full status and results for a prospecting run."""
    detail = await run_store.aget_detail(run_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return detail


@app.get("/api/prospect/{run_id}/stream", tags=["prospecting"])
async def stream_run_progress(run_id: str):
    """SSE endpoint for real-time node progress updates."""
    run = await run_store.aget_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        queue = run_store.subscribe(run_id)
        try:
            # If already completed, send final state immediately
            current = await run_store.aget_run(run_id)
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
    return await run_store.alist_runs()


# --- Project endpoints ---


@app.post("/api/projects", response_model=ProjectSummary, status_code=201, tags=["projects"])
async def create_project(request: CreateProjectRequest):
    """Create a new project."""
    project_id = project_store.create_project(
        client_name=request.client_name,
        tags=request.tags,
        notes=request.notes,
    )
    projects = project_store.list_projects(run_store)
    return next(p for p in projects if p.project_id == project_id)


@app.get("/api/projects", response_model=list[ProjectSummary], tags=["projects"])
async def list_projects():
    """List all projects, most recently updated first."""
    return project_store.list_projects(run_store)


@app.get("/api/projects/{project_id}", response_model=ProjectDetail, tags=["projects"])
async def get_project(project_id: str):
    """Get full project detail including iterations and saved plays."""
    detail = project_store.get_project_detail(project_id, run_store)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return detail


@app.patch("/api/projects/{project_id}", response_model=ProjectSummary, tags=["projects"])
async def update_project(project_id: str, request: UpdateProjectRequest):
    """Update project metadata."""
    updates = request.model_dump(exclude_none=True)
    if not project_store.update_project(project_id, updates):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    projects = project_store.list_projects(run_store)
    return next(p for p in projects if p.project_id == project_id)


@app.delete("/api/projects/{project_id}", status_code=204, tags=["projects"])
async def delete_project(project_id: str):
    """Delete a project. Does not delete associated runs."""
    if not project_store.delete_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return None


@app.post("/api/projects/{project_id}/iterate", response_model=RunSummary, status_code=202, tags=["projects"])
async def start_iteration(project_id: str, request: IterateRequest, background_tasks: BackgroundTasks):
    """Start a new iteration within a project.

    If build_on_previous is True and parent_iteration_id is provided (or the project
    has previous iterations), the new run will include context from the previous iteration.
    """
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Build previous context if requested
    previous_context: Optional[dict] = None

    if request.build_on_previous:
        # Determine which iteration to build on
        parent_id = request.parent_iteration_id
        if not parent_id and proj["iteration_ids"]:
            parent_id = proj["iteration_ids"][-1]  # most recent

        if parent_id:
            parent_detail = run_store.get_detail(parent_id)
            if parent_detail and parent_detail.status == RunStatus.COMPLETED:
                previous_context = {
                    "deep_research_report": parent_detail.deep_research_report,
                    "competitor_proofs": parent_detail.competitor_proofs,
                }
            elif parent_detail and parent_detail.status != RunStatus.COMPLETED:
                raise HTTPException(
                    status_code=409,
                    detail=f"Parent iteration {parent_id} is not completed (status: {parent_detail.status})",
                )
            else:
                raise HTTPException(status_code=404, detail=f"Parent iteration {parent_id} not found")

    run_id = run_store.create_run(
        client_name=proj["client_name"],
        past_sales_history=request.past_sales_history,
        base_research_prompt=request.base_research_prompt,
        project_id=project_id,
    )

    project_store.add_iteration(project_id, run_id)

    background_tasks.add_task(
        _run_pipeline,
        run_id=run_id,
        client_name=proj["client_name"],
        past_sales_history=request.past_sales_history,
        base_research_prompt=request.base_research_prompt,
        previous_context=previous_context,
    )

    runs = run_store.list_runs()
    return next(r for r in runs if r.run_id == run_id)


@app.post("/api/projects/{project_id}/plays", response_model=SavedPlay, status_code=201, tags=["projects"])
async def save_play(project_id: str, request: SavePlayRequest):
    """Save a specific play from an iteration into the project's saved plays."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Get the iteration's results
    detail = run_store.get_detail(request.iteration_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Iteration {request.iteration_id} not found")

    if detail.status != RunStatus.COMPLETED:
        raise HTTPException(status_code=409, detail=f"Iteration {request.iteration_id} is not completed")

    if request.play_index < 0 or request.play_index >= len(detail.refined_plays):
        raise HTTPException(
            status_code=400,
            detail=f"play_index {request.play_index} out of range (0-{len(detail.refined_plays) - 1})",
        )

    play_data = detail.refined_plays[request.play_index]
    play_id = project_store.save_play(
        project_id=project_id,
        iteration_id=request.iteration_id,
        play_data=play_data,
        notes=request.notes,
    )

    if not play_id:
        raise HTTPException(status_code=500, detail="Failed to save play")

    # Return the saved play
    project_detail = project_store.get_project_detail(project_id, run_store)
    return next(sp for sp in project_detail.saved_plays if sp.play_id == play_id)


@app.delete("/api/projects/{project_id}/plays/{play_id}", status_code=204, tags=["projects"])
async def remove_saved_play(project_id: str, play_id: str):
    """Remove a saved play from a project."""
    if not project_store.remove_saved_play(project_id, play_id):
        raise HTTPException(status_code=404, detail=f"Play {play_id} not found in project {project_id}")
    return None
