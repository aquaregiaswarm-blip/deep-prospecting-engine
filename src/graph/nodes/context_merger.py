"""Context Merger node — combines research, history, and ChromaDB context."""

from __future__ import annotations

import logging

from src.graph.state import ProspectingState
from src.memory.chroma_query import query_similar_verticals, query_similar_plays
from src.config import get_settings

logger = logging.getLogger(__name__)


def context_merger(state: ProspectingState) -> dict:
    """Merge deep research output with historical context from ChromaDB.
    
    Reads: client_vertical, client_domain, deep_research_report
    Writes: similar_verticals, similar_plays, current_step
    """
    logger.info("Merging context for %s [%s/%s]",
                state.client_name, state.client_vertical, state.client_domain)

    settings = get_settings()

    # Query ChromaDB for similar verticals
    similar_verticals = query_similar_verticals(
        persist_dir=settings.chroma_persist_dir,
        vertical=state.client_vertical,
        domain=state.client_domain,
    )

    # Query ChromaDB for similar plays
    similar_plays = query_similar_plays(
        persist_dir=settings.chroma_persist_dir,
        vertical=state.client_vertical,
        research_summary=state.deep_research_report[:1000],
    )

    logger.info(
        "Context merged: %d similar verticals, %d similar plays",
        len(similar_verticals),
        len(similar_plays),
    )

    return {
        "similar_verticals": similar_verticals,
        "similar_plays": similar_plays,
        "current_step": "context_merged",
    }
