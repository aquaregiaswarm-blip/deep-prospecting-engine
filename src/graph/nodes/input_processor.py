"""Input Processor node — validates and prepares user input for the pipeline."""

from __future__ import annotations

import logging
from src.graph.state import ProspectingState
from src.prompts.base_research import DEFAULT_BASE_PROMPT

logger = logging.getLogger(__name__)


def input_processor(state: ProspectingState) -> dict:
    """Validate inputs and prepare the base research prompt.
    
    Reads: client_name, past_sales_history, base_research_prompt
    Writes: base_research_prompt (populated if empty), current_step
    """
    logger.info("Processing input for client: %s", state.client_name)

    errors = []

    if not state.client_name or not state.client_name.strip():
        errors.append("Client name is required.")

    if not state.past_sales_history or not state.past_sales_history.strip():
        logger.warning("No past sales history provided — proceeding without it.")

    # Set default research prompt if none provided
    base_prompt = state.base_research_prompt
    if not base_prompt or not base_prompt.strip():
        base_prompt = DEFAULT_BASE_PROMPT.format(
            client_name=state.client_name,
            additional_focus="",
        )
    else:
        # Ensure client name is injected if user provided a custom prompt
        if "{client_name}" in base_prompt:
            base_prompt = base_prompt.format(
                client_name=state.client_name,
                additional_focus="",
            )

    return {
        "base_research_prompt": base_prompt,
        "current_step": "input_processed",
        "errors": errors,
    }
