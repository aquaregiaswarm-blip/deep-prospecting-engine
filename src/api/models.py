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
