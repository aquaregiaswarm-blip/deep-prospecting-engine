"""Pydantic request/response models for the API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Possible states for a prospecting run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProspectRequest(BaseModel):
    """Request body for starting a new prospecting run."""
    client_name: str = Field(..., min_length=1, max_length=200, description="Target client name")
    past_sales_history: str = Field(default="", description="Prior sales history or relationship context")
    base_research_prompt: str = Field(default="", description="Custom research prompt override")
    project_id: Optional[str] = Field(default=None, description="Optional project to attach this run to")


class RunSummary(BaseModel):
    """Summary of a prospecting run for list views."""
    run_id: str
    client_name: str
    status: RunStatus
    current_step: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    plays_count: int = 0
    error: Optional[str] = None
    project_id: Optional[str] = None


class RunDetail(RunSummary):
    """Full detail of a prospecting run including results."""
    deep_research_report: str = ""
    client_vertical: str = ""
    client_domain: str = ""
    digital_maturity_summary: str = ""
    competitor_proofs: list[dict] = Field(default_factory=list)
    refined_plays: list[dict] = Field(default_factory=list)
    one_pagers: dict[str, str] = Field(default_factory=dict)
    strategic_plan: str = ""
    errors: list[str] = Field(default_factory=list)


class NodeProgress(BaseModel):
    """SSE event payload for node progress updates."""
    run_id: str
    node: str
    status: str  # "started" | "completed" | "failed"
    timestamp: datetime
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "deep-prospecting-engine"


# --- Project & Iteration models ---


class SavedPlay(BaseModel):
    """A play saved from a run iteration into a project."""
    play_id: str
    iteration_id: str  # which run it came from
    play_data: dict  # the actual play content
    notes: str = ""
    saved_at: datetime


class ProjectSummary(BaseModel):
    """Summary of a project for list views."""
    project_id: str
    client_name: str
    created_at: datetime
    updated_at: datetime
    iteration_count: int = 0
    latest_status: Optional[RunStatus] = None
    saved_plays_count: int = 0
    tags: list[str] = Field(default_factory=list)


class ProjectDetail(ProjectSummary):
    """Full project detail including iterations and saved plays."""
    notes: str = ""
    iterations: list[RunSummary] = Field(default_factory=list)
    saved_plays: list[SavedPlay] = Field(default_factory=list)


class CreateProjectRequest(BaseModel):
    """Request body for creating a new project."""
    client_name: str = Field(..., min_length=1, max_length=200)
    tags: list[str] = Field(default_factory=list)
    notes: str = ""


class UpdateProjectRequest(BaseModel):
    """Request body for updating a project."""
    client_name: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None


class IterateRequest(BaseModel):
    """Start a new iteration within a project. Inherits context from parent if specified."""
    past_sales_history: str = ""
    base_research_prompt: str = ""
    parent_iteration_id: Optional[str] = None  # fork from this iteration
    build_on_previous: bool = False  # feed previous research into this run


class SavePlayRequest(BaseModel):
    """Request to save a play from a run iteration."""
    iteration_id: str
    play_index: int  # index in refined_plays
    notes: str = ""
