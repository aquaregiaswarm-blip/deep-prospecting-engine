"""LangGraph workflow definition for the Deep Prospecting Engine.

Defines the full agent pipeline:
  Input → Deep Research → Context Merger → Competitor Scout → 
  Divergent Ideation → Convergent Refinement → Asset Generation → Store
"""

from __future__ import annotations

import logging
from dataclasses import asdict

from langgraph.graph import StateGraph, END

from src.graph.state import ProspectingState
from src.graph.nodes import (
    input_processor,
    deep_research,
    context_merger,
    competitor_scout,
    divergent_ideation,
    convergent_refinement,
    asset_generator,
)
from src.memory.chroma_store import store_plays, store_client_profile
from src.config import get_settings

logger = logging.getLogger(__name__)


def _knowledge_capture(state: ProspectingState) -> dict:
    """Store completed plays back into ChromaDB for future learning."""
    settings = get_settings()
    plays_stored = store_plays(settings.chroma_persist_dir, state)
    profile_stored = store_client_profile(settings.chroma_persist_dir, state)
    logger.info(
        "Knowledge capture: %d plays stored, profile=%s",
        plays_stored, profile_stored,
    )
    return {"current_step": "complete"}


def _should_continue_after_research(state: ProspectingState) -> str:
    """Route after research — continue or abort on failure."""
    if state.current_step == "research_failed":
        return "end"
    return "context_merger"


def _should_continue_after_ideation(state: ProspectingState) -> str:
    """Route after ideation — continue or abort if no ideas."""
    if not state.raw_ideas:
        return "end"
    return "convergent_refinement"


def _should_continue_after_refinement(state: ProspectingState) -> str:
    """Route after refinement — continue or abort if no plays."""
    if not state.refined_plays:
        return "end"
    return "asset_generator"


def build_workflow() -> StateGraph:
    """Build and compile the LangGraph workflow.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Note: LangGraph uses dict-based state by default.
    # We use ProspectingState as a dataclass but nodes return dicts
    # that get merged into the state.
    workflow = StateGraph(ProspectingState)

    # Add nodes
    workflow.add_node("input_processor", input_processor)
    workflow.add_node("deep_research", deep_research)
    workflow.add_node("context_merger", context_merger)
    workflow.add_node("competitor_scout", competitor_scout)
    workflow.add_node("divergent_ideation", divergent_ideation)
    workflow.add_node("convergent_refinement", convergent_refinement)
    workflow.add_node("asset_generator", asset_generator)
    workflow.add_node("knowledge_capture", _knowledge_capture)

    # Define edges
    workflow.set_entry_point("input_processor")
    workflow.add_edge("input_processor", "deep_research")
    workflow.add_conditional_edges(
        "deep_research",
        _should_continue_after_research,
        {"context_merger": "context_merger", "end": END},
    )
    workflow.add_edge("context_merger", "competitor_scout")
    workflow.add_edge("competitor_scout", "divergent_ideation")
    workflow.add_conditional_edges(
        "divergent_ideation",
        _should_continue_after_ideation,
        {"convergent_refinement": "convergent_refinement", "end": END},
    )
    workflow.add_conditional_edges(
        "convergent_refinement",
        _should_continue_after_refinement,
        {"asset_generator": "asset_generator", "end": END},
    )
    workflow.add_edge("asset_generator", "knowledge_capture")
    workflow.add_edge("knowledge_capture", END)

    return workflow.compile()


def run_prospecting(
    client_name: str,
    past_sales_history: str = "",
    base_research_prompt: str = "",
) -> ProspectingState:
    """Run the full prospecting pipeline.
    
    Args:
        client_name: Target client name
        past_sales_history: Optional past sales history text
        base_research_prompt: Optional custom research prompt
        
    Returns:
        Final ProspectingState with all results
    """
    logger.info("Starting prospecting run for: %s", client_name)

    app = build_workflow()

    initial_state = ProspectingState(
        client_name=client_name,
        past_sales_history=past_sales_history,
        base_research_prompt=base_research_prompt,
    )

    final_state = app.invoke(initial_state)

    logger.info("Prospecting complete. Step: %s", final_state.current_step)
    return final_state
