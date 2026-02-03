"""Shared test fixtures for the Deep Prospecting Engine."""

import os
import pytest
from unittest.mock import patch

from src.graph.state import (
    ProspectingState,
    Citation,
    CompetitorProof,
    SalesPlay,
    HistoricalPlay,
)


@pytest.fixture(autouse=True)
def mock_env():
    """Ensure tests don't hit real APIs."""
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test-key-not-real",
        "CHROMA_PERSIST_DIR": "/tmp/test_chromadb",
        "OUTPUT_DIR": "/tmp/test_output",
    }):
        yield


@pytest.fixture
def sample_state() -> ProspectingState:
    """A populated sample state for testing."""
    return ProspectingState(
        client_name="Acme Corp",
        past_sales_history="2023: Sold 500 Cloud Storage licenses. 2024: Sold 200 Compute instances.",
        base_research_prompt="Research Acme Corp's AI initiatives.",
    )


@pytest.fixture
def sample_citation() -> Citation:
    return Citation(
        title="Acme AI Strategy",
        url="https://example.com/acme-ai",
        snippet="Acme is investing heavily in AI.",
    )


@pytest.fixture
def sample_competitor_proof() -> CompetitorProof:
    return CompetitorProof(
        competitor_name="RivalCo",
        vertical="Manufacturing",
        use_case="Predictive maintenance using IoT + ML",
        outcome="30% reduction in downtime",
        source=Citation(
            title="RivalCo Case Study",
            url="https://rivalco.com/case-study",
            snippet="",
        ),
    )


@pytest.fixture
def sample_sales_play() -> SalesPlay:
    return SalesPlay(
        title="AI-Powered Quality Inspection",
        challenge="Manual quality inspection is slow and error-prone",
        market_standard="Competitors use computer vision for automated inspection",
        proposed_solution="Deploy edge-based CV models for real-time defect detection",
        business_outcome="50% reduction in defect escape rate",
        technical_stack=["TensorFlow", "Edge TPU", "GCP Vertex AI"],
        confidence_score=0.85,
        citations=[],
    )


@pytest.fixture
def sample_historical_play() -> HistoricalPlay:
    return HistoricalPlay(
        client_name="PastClient Inc",
        vertical="Manufacturing",
        play_summary="Deployed predictive maintenance solution",
        outcome="Reduced unplanned downtime by 40%",
        similarity_score=0.82,
    )


@pytest.fixture
def researched_state(
    sample_state, sample_citation, sample_competitor_proof, sample_sales_play
) -> ProspectingState:
    """A state that has been through research and ideation."""
    state = sample_state
    state.deep_research_report = "Acme Corp is a major manufacturing company..."
    state.research_citations = [sample_citation]
    state.client_vertical = "Manufacturing"
    state.client_domain = "Discrete Manufacturing"
    state.digital_maturity_summary = "Level 3 - Developing"
    state.competitor_proofs = [sample_competitor_proof]
    state.history_synthesis = "Bought storage but no compute — ML modernization play."
    state.history_gaps = ["No ML compute", "No data pipeline"]
    state.raw_ideas = [sample_sales_play]
    state.refined_plays = [sample_sales_play]
    return state
