"""Asset Generator node — produces Pellera-voiced markdown deliverables."""

from __future__ import annotations

import logging
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai

from src.graph.state import ProspectingState
from src.prompts.pellera_voice import (
    PELLERA_SYSTEM_PROMPT,
    ONE_PAGER_TEMPLATE,
    STRATEGIC_PLAN_TEMPLATE,
)
from src.config import get_settings

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Call Gemini with system prompt and retry logic."""
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=system_prompt,
    )
    response = model.generate_content(user_prompt)
    return response.text


def _generate_one_pager(play: dict, state: ProspectingState) -> str:
    """Generate a one-pager markdown for a single play."""
    prompt = f"""Write a compelling one-pager for the following AI sales play.

Client: {state.client_name}
Vertical: {state.client_vertical}

Play: {play['title']}
Challenge: {play['challenge']}
Market Standard: {play.get('market_standard', 'See competitor analysis')}
Proposed Solution: {play['proposed_solution']}
Business Outcome: {play['business_outcome']}
Technical Stack: {', '.join(play.get('technical_stack', []))}

Competitor Context:
{_format_proofs(state.competitor_proofs)}

Use this structure:
1. The Challenge — paint the pain vividly
2. The Market Standard — what competitors are doing (create urgency)
3. The Pellera Solution — our specific approach and why it's superior
4. The Business Outcome — quantified or strongly directional impact

Include source citations as footnotes where applicable.
End with a clear next step / call to action.
"""
    return _call_gemini(PELLERA_SYSTEM_PROMPT, prompt)


def _generate_strategic_plan(state: ProspectingState) -> str:
    """Generate a consolidated strategic account plan."""
    plays_summary = "\n\n".join(
        f"### {i+1}. {p['title']}\n{p['challenge']} → {p['proposed_solution']} → {p['business_outcome']}"
        for i, p in enumerate(state.refined_plays)
    )

    prompt = f"""Write a Strategic Account Plan for {state.client_name}.

Client Vertical: {state.client_vertical} / {state.client_domain}
Digital Maturity: {state.digital_maturity_summary}

Deep Research Summary:
{state.deep_research_report[:3000]}

Sales History Analysis:
{state.history_synthesis[:1500]}

Competitive Landscape:
{_format_proofs(state.competitor_proofs)}

Recommended Plays:
{plays_summary}

Structure:
1. Executive Summary (2-3 paragraphs)
2. Client Profile (key facts)
3. Current State Assessment
4. Sales History & Relationship Summary
5. Competitive Landscape Analysis
6. Recommended AI Initiatives (detail each play)
7. Implementation Roadmap (phased, realistic)
8. Risk Factors

Include all source citations. Make it boardroom-ready.
"""
    return _call_gemini(PELLERA_SYSTEM_PROMPT, prompt)


def _format_proofs(proofs: list) -> str:
    """Format competitor proofs for prompt context."""
    if not proofs:
        return "No competitor data available."
    lines = []
    for p in proofs:
        source_info = f" (Source: {p['source']['url']})" if p.get("source", {}).get("url") else ""
        lines.append(f"- {p['competitor_name']}: {p['use_case']} → {p['outcome']}{source_info}")
    return "\n".join(lines)


def _save_markdown(output_dir: str, filename: str, content: str) -> str:
    """Save markdown content to file."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / filename
    filepath.write_text(content, encoding="utf-8")
    logger.info("Saved: %s", filepath)
    return str(filepath)


def asset_generator(state: ProspectingState) -> dict:
    """Generate all client-ready markdown assets.
    
    Reads: refined_plays, client_name, all context
    Writes: one_pagers, strategic_plan, current_step
    """
    logger.info("Generating assets for %s (%d plays)", state.client_name, len(state.refined_plays))
    settings = get_settings()

    if not state.refined_plays:
        return {
            "errors": state.errors + ["No plays to generate assets for."],
            "current_step": "asset_generation_failed",
        }

    try:
        one_pagers = {}

        # Generate one-pagers for each play
        for play in state.refined_plays:
            title = play["title"]
            logger.info("Generating one-pager: %s", title)
            content = _generate_one_pager(play, state)
            one_pagers[title] = content

            # Save to file
            safe_name = title.lower().replace(" ", "_")[:50]
            client_safe = state.client_name.lower().replace(" ", "_")[:30]
            _save_markdown(
                settings.output_dir,
                f"{client_safe}_{safe_name}_one_pager.md",
                content,
            )

        # Generate strategic plan
        logger.info("Generating strategic account plan")
        strategic_plan = _generate_strategic_plan(state)
        client_safe = state.client_name.lower().replace(" ", "_")[:30]
        _save_markdown(
            settings.output_dir,
            f"{client_safe}_strategic_plan.md",
            strategic_plan,
        )

        return {
            "one_pagers": one_pagers,
            "strategic_plan": strategic_plan,
            "current_step": "assets_generated",
        }

    except Exception as e:
        logger.error("Asset generation failed: %s", e)
        return {
            "errors": state.errors + [f"Asset generation failed: {str(e)}"],
            "current_step": "asset_generation_failed",
        }
