"""Deep Research node — calls Gemini to produce a comprehensive client report."""

from __future__ import annotations

import json
import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai

from src.graph.state import ProspectingState, Citation
from src.prompts.base_research import VERTICAL_CLASSIFICATION_PROMPT, HISTORY_SYNTHESIS_PROMPT
from src.config import get_settings

logger = logging.getLogger(__name__)


def _get_model(model_name: str | None = None) -> genai.GenerativeModel:
    """Initialize and return a Gemini model."""
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(model_name or settings.gemini_research_model)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _call_gemini(model: genai.GenerativeModel, prompt: str) -> str:
    """Call Gemini with retry logic."""
    response = model.generate_content(prompt)
    return response.text


def _extract_citations(report: str) -> list[Citation]:
    """Extract URLs and their context from the research report."""
    import re
    citations = []
    # Match markdown-style links [text](url)
    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    for match in re.finditer(pattern, report):
        citations.append(Citation(
            title=match.group(1),
            url=match.group(2),
            snippet="",
        ))
    # Match bare URLs
    bare_url_pattern = r'(?<!\()(?<!\[)(https?://[^\s,\)\]]+)'
    seen_urls = {c["url"] for c in citations}
    for match in re.finditer(bare_url_pattern, report):
        url = match.group(1)
        if url not in seen_urls:
            citations.append(Citation(title="", url=url, snippet=""))
            seen_urls.add(url)
    return citations


def _classify_vertical(model: genai.GenerativeModel, report: str) -> dict[str, Any]:
    """Parse the research report to classify vertical and domain."""
    prompt = VERTICAL_CLASSIFICATION_PROMPT.format(report=report[:8000])
    response = _call_gemini(model, prompt)
    try:
        # Try to extract JSON from the response
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        return json.loads(json_str.strip())
    except (json.JSONDecodeError, IndexError):
        logger.warning("Failed to parse vertical classification, using defaults")
        return {
            "vertical": "Unknown",
            "domain": "Unknown",
            "maturity_level": 0,
            "maturity_summary": "Could not classify",
        }


def _synthesize_history(
    model: genai.GenerativeModel,
    client_name: str,
    vertical: str,
    sales_history: str,
) -> dict[str, Any]:
    """Analyze past sales history for gaps and opportunities."""
    if not sales_history.strip():
        return {"gaps": [], "synthesis": "No sales history provided."}

    prompt = HISTORY_SYNTHESIS_PROMPT.format(
        client_name=client_name,
        vertical=vertical,
        sales_history=sales_history,
    )
    response = _call_gemini(model, prompt)
    return {"gaps": [], "synthesis": response}


def deep_research(state: ProspectingState) -> dict:
    """Execute deep research on the client using Gemini.
    
    Reads: client_name, base_research_prompt, past_sales_history
    Writes: deep_research_report, research_citations, client_vertical,
            client_domain, digital_maturity_summary, history_gaps, history_synthesis
    """
    logger.info("Starting deep research for: %s", state.client_name)

    try:
        model = _get_model()

        # 1. Deep research report
        report = _call_gemini(model, state.base_research_prompt)
        citations = _extract_citations(report)

        # 2. Classify vertical
        classification = _classify_vertical(model, report)

        # 3. Synthesize sales history
        history = _synthesize_history(
            model,
            state.client_name,
            classification.get("vertical", "Unknown"),
            state.past_sales_history,
        )

        return {
            "deep_research_report": report,
            "research_citations": citations,
            "client_vertical": classification.get("vertical", "Unknown"),
            "client_domain": classification.get("domain", "Unknown"),
            "digital_maturity_summary": classification.get("maturity_summary", ""),
            "history_gaps": history.get("gaps", []),
            "history_synthesis": history.get("synthesis", ""),
            "current_step": "research_complete",
        }

    except Exception as e:
        logger.error("Deep research failed: %s", e)
        return {
            "errors": state.errors + [f"Deep research failed: {str(e)}"],
            "current_step": "research_failed",
        }
