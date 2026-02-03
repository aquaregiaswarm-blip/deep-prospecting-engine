"""Id8 Ideation Loop — divergent generation and convergent refinement."""

from __future__ import annotations

import json
import logging

from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai

from src.graph.state import ProspectingState, SalesPlay, Citation
from src.prompts.ideation import DIVERGENT_PROMPT, CONVERGENT_PROMPT
from src.config import get_settings

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _call_gemini(prompt: str) -> str:
    """Call Gemini with retry logic."""
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    response = model.generate_content(prompt)
    return response.text


def _parse_plays(response: str) -> list[SalesPlay]:
    """Parse Gemini response into SalesPlay objects."""
    try:
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]

        data = json.loads(json_str.strip())
        plays = []
        for item in data:
            plays.append(SalesPlay(
                title=item.get("title", "Untitled"),
                challenge=item.get("challenge", ""),
                market_standard=item.get("market_standard", ""),
                proposed_solution=item.get("proposed_solution", ""),
                business_outcome=item.get("business_outcome", ""),
                technical_stack=item.get("technical_stack", []),
                confidence_score=float(item.get("confidence_score", 0.5)),
                citations=item.get("citations", []),
            ))
        return plays
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning("Failed to parse plays: %s", e)
        return []


def _format_competitor_proofs(proofs: list) -> str:
    """Format competitor proofs for prompt injection."""
    if not proofs:
        return "No competitor data available."
    lines = []
    for p in proofs:
        lines.append(f"- **{p['competitor_name']}**: {p['use_case']} → {p['outcome']}")
    return "\n".join(lines)


def _format_historical_plays(plays: list) -> str:
    """Format historical plays for prompt injection."""
    if not plays:
        return "No historical data yet (cold start)."
    lines = []
    for p in plays:
        lines.append(
            f"- **{p['client_name']}** ({p['vertical']}): {p['play_summary'][:200]} "
            f"[similarity: {p['similarity_score']:.2f}]"
        )
    return "\n".join(lines)


def divergent_ideation(state: ProspectingState) -> dict:
    """Generate 10+ raw AI use case ideas.
    
    Reads: client_name, client_vertical, client_domain, deep_research_report,
           history_gaps, history_synthesis, competitor_proofs, similar_plays
    Writes: raw_ideas, current_step
    """
    logger.info("Starting divergent ideation for %s", state.client_name)
    settings = get_settings()

    try:
        prompt = DIVERGENT_PROMPT.format(
            client_name=state.client_name,
            vertical=state.client_vertical,
            domain=state.client_domain,
            research_summary=state.deep_research_report[:3000],
            history_gaps="\n".join(f"- {g}" for g in state.history_gaps) if state.history_gaps else state.history_synthesis[:1000],
            competitor_proofs=_format_competitor_proofs(state.competitor_proofs),
            historical_plays=_format_historical_plays(state.similar_plays),
            min_ideas=settings.min_ideas,
        )

        response = _call_gemini(prompt)
        ideas = _parse_plays(response)

        logger.info("Generated %d raw ideas", len(ideas))

        return {
            "raw_ideas": ideas,
            "current_step": "ideas_generated",
        }

    except Exception as e:
        logger.error("Divergent ideation failed: %s", e)
        return {
            "errors": state.errors + [f"Ideation failed: {str(e)}"],
            "current_step": "ideation_failed",
        }


def convergent_refinement(state: ProspectingState) -> dict:
    """Filter and refine raw ideas down to top N plays.
    
    Reads: raw_ideas
    Writes: refined_plays, current_step
    """
    logger.info("Starting convergent refinement: %d raw ideas", len(state.raw_ideas))
    settings = get_settings()

    if not state.raw_ideas:
        logger.warning("No raw ideas to refine.")
        return {
            "refined_plays": [],
            "errors": state.errors + ["No raw ideas generated for refinement."],
            "current_step": "refinement_failed",
        }

    try:
        raw_json = json.dumps([dict(p) for p in state.raw_ideas], indent=2)

        prompt = CONVERGENT_PROMPT.format(
            raw_ideas=raw_json,
            top_plays=settings.top_plays,
        )

        response = _call_gemini(prompt)
        refined = _parse_plays(response)

        # Ensure we don't exceed top_plays
        refined = refined[:settings.top_plays]

        logger.info("Refined to %d top plays", len(refined))

        return {
            "refined_plays": refined,
            "current_step": "plays_refined",
        }

    except Exception as e:
        logger.error("Convergent refinement failed: %s", e)
        return {
            "errors": state.errors + [f"Refinement failed: {str(e)}"],
            "current_step": "refinement_failed",
        }
