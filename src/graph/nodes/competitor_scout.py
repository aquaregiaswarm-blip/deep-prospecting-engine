"""Competitor Scout node — finds competitor AI case studies for FOMO leverage."""

from __future__ import annotations

import json
import logging

from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai

from src.graph.state import ProspectingState, CompetitorProof, Citation
from src.config import get_settings

logger = logging.getLogger(__name__)

COMPETITOR_SCOUT_PROMPT = """You are a competitive intelligence analyst. Based on the following research about {client_name} in the {vertical} vertical:

{research_excerpt}

Find and describe competitor AI/ML initiatives in this vertical. For each competitor:
1. **Competitor Name**: Who they are
2. **Use Case**: What AI/ML initiative they've published or announced
3. **Outcome**: Reported results or benefits
4. **Source**: URL or publication reference

Focus on real, verifiable case studies — not speculation. These will be used as "proof points" to demonstrate market movement and create urgency.

Return as a JSON array:
[{{"competitor_name": "...", "use_case": "...", "outcome": "...", "source_title": "...", "source_url": "..."}}]

Find at least 3-5 competitors if possible.
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _call_gemini(prompt: str) -> str:
    """Call Gemini with retry logic."""
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    response = model.generate_content(prompt)
    return response.text


def _parse_competitors(response: str) -> list[CompetitorProof]:
    """Parse Gemini response into CompetitorProof objects."""
    try:
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]

        data = json.loads(json_str.strip())
        proofs = []
        for item in data:
            proofs.append(CompetitorProof(
                competitor_name=item.get("competitor_name", "Unknown"),
                vertical=item.get("vertical", ""),
                use_case=item.get("use_case", ""),
                outcome=item.get("outcome", ""),
                source=Citation(
                    title=item.get("source_title", ""),
                    url=item.get("source_url", ""),
                    snippet="",
                ),
            ))
        return proofs
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.warning("Failed to parse competitor data: %s", e)
        return []


def competitor_scout(state: ProspectingState) -> dict:
    """Search for competitor AI case studies in the client's vertical.
    
    Reads: client_name, client_vertical, deep_research_report
    Writes: competitor_proofs, current_step
    """
    logger.info("Scouting competitors for %s in %s", state.client_name, state.client_vertical)

    try:
        prompt = COMPETITOR_SCOUT_PROMPT.format(
            client_name=state.client_name,
            vertical=state.client_vertical,
            research_excerpt=state.deep_research_report[:4000],
        )

        response = _call_gemini(prompt)
        proofs = _parse_competitors(response)

        logger.info("Found %d competitor proof points", len(proofs))

        return {
            "competitor_proofs": proofs,
            "current_step": "competitors_scouted",
        }

    except Exception as e:
        logger.error("Competitor scouting failed: %s", e)
        return {
            "errors": state.errors + [f"Competitor scouting failed: {str(e)}"],
            "current_step": "competitors_failed",
        }
