"""Deep Research node — calls Gemini with Google Search grounding for real web research."""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from src.graph.state import ProspectingState, Citation
from src.prompts.base_research import VERTICAL_CLASSIFICATION_PROMPT, HISTORY_SYNTHESIS_PROMPT
from src.config import get_settings

logger = logging.getLogger(__name__)


def _get_client() -> genai.Client:
    """Initialize and return a Gemini client."""
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)


def _get_model_name() -> str:
    """Get the research model name from settings."""
    settings = get_settings()
    return settings.gemini_research_model


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _call_gemini_with_search(client: genai.Client, prompt: str, model_name: str | None = None) -> tuple[str, list[Citation]]:
    """Call Gemini with Google Search grounding for real web research.
    
    Returns (response_text, citations).
    """
    model = model_name or _get_model_name()
    
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.7,
        ),
    )
    
    text = response.text or ""
    citations = []
    
    # Extract citations from grounding metadata
    if response.candidates and response.candidates[0].grounding_metadata:
        gm = response.candidates[0].grounding_metadata
        if gm.grounding_chunks:
            for chunk in gm.grounding_chunks:
                if chunk.web:
                    citations.append(Citation(
                        title=chunk.web.title or "",
                        url=chunk.web.uri or "",
                        snippet="",
                    ))
        
        # Also extract inline citations from grounding supports
        if gm.grounding_supports:
            for support in gm.grounding_supports:
                if support.segment and support.grounding_chunk_indices:
                    snippet = support.segment.text or ""
                    for idx in support.grounding_chunk_indices:
                        if idx < len(citations) and citations[idx].get("snippet") == "":
                            citations[idx]["snippet"] = snippet[:200]
    
    # Also extract any markdown-style citations from the text itself
    import re
    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    seen_urls = {c["url"] for c in citations}
    for match in re.finditer(pattern, text):
        url = match.group(2)
        if url not in seen_urls:
            citations.append(Citation(
                title=match.group(1),
                url=url,
                snippet="",
            ))
            seen_urls.add(url)
    
    return text, citations


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _call_gemini(client: genai.Client, prompt: str, model_name: str | None = None) -> str:
    """Call Gemini without search grounding (for classification/synthesis tasks)."""
    model = model_name or _get_model_name()
    
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
        ),
    )
    
    return response.text or ""


def _classify_vertical(client: genai.Client, report: str) -> dict[str, Any]:
    """Parse the research report to classify vertical and domain."""
    prompt = VERTICAL_CLASSIFICATION_PROMPT.format(report=report[:8000])
    response = _call_gemini(client, prompt)
    try:
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
    client: genai.Client,
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
    response = _call_gemini(client, prompt)
    return {"gaps": [], "synthesis": response}


def deep_research(state: ProspectingState) -> dict:
    """Execute deep research on the client using Gemini with Google Search grounding.
    
    This uses real-time web search to produce grounded, cited research reports
    rather than relying solely on the model's training data.
    
    Reads: client_name, base_research_prompt, past_sales_history
    Writes: deep_research_report, research_citations, client_vertical,
            client_domain, digital_maturity_summary, history_gaps, history_synthesis
    """
    logger.info("Starting deep research (with web grounding) for: %s", state.client_name)

    try:
        client = _get_client()

        # 1. Deep research report WITH web search grounding
        logger.info("Running grounded web research for %s", state.client_name)
        report, citations = _call_gemini_with_search(client, state.base_research_prompt)
        logger.info("Research complete: %d chars, %d citations", len(report), len(citations))

        # 2. Classify vertical (no search needed)
        classification = _classify_vertical(client, report)

        # 3. Synthesize sales history (no search needed)
        history = _synthesize_history(
            client,
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
