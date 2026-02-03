"""LangGraph state schema for the Deep Prospecting Engine.

The state flows through all nodes, accumulating data at each stage.
Citations are carried from deep research through to final asset generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


class Citation(TypedDict):
    """A source citation from research."""
    title: str
    url: str
    snippet: str


class CompetitorProof(TypedDict):
    """A competitor's AI case study used as leverage."""
    competitor_name: str
    vertical: str
    use_case: str
    outcome: str
    source: Citation


class SalesPlay(TypedDict):
    """A proposed AI sales play for the client."""
    title: str
    challenge: str
    market_standard: str  # What competitors are doing
    proposed_solution: str
    business_outcome: str
    technical_stack: list[str]
    confidence_score: float  # 0.0 - 1.0
    citations: list[Citation]


class HistoricalPlay(TypedDict):
    """A past successful play retrieved from ChromaDB."""
    client_name: str
    vertical: str
    play_summary: str
    outcome: str
    similarity_score: float


@dataclass
class ProspectingState:
    """The central state object passed through the LangGraph workflow.
    
    Each node reads what it needs and writes its outputs back to this state.
    """

    # --- Input (from UI) ---
    client_name: str = ""
    past_sales_history: str = ""
    base_research_prompt: str = ""

    # --- Deep Research Output ---
    deep_research_report: str = ""
    research_citations: list[Citation] = field(default_factory=list)
    client_vertical: str = ""
    client_domain: str = ""
    digital_maturity_summary: str = ""

    # --- Memory / Historical Context ---
    similar_verticals: list[HistoricalPlay] = field(default_factory=list)
    similar_plays: list[HistoricalPlay] = field(default_factory=list)

    # --- Competitor Analysis ---
    competitor_proofs: list[CompetitorProof] = field(default_factory=list)

    # --- History Synthesis ---
    history_gaps: list[str] = field(default_factory=list)
    history_synthesis: str = ""

    # --- Ideation ---
    raw_ideas: list[SalesPlay] = field(default_factory=list)
    refined_plays: list[SalesPlay] = field(default_factory=list)

    # --- Asset Generation ---
    one_pagers: dict[str, str] = field(default_factory=dict)  # title -> markdown
    strategic_plan: str = ""

    # --- Metadata ---
    errors: list[str] = field(default_factory=list)
    current_step: str = "initialized"
