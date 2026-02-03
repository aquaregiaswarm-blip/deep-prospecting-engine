"""Tests for the Id8 Ideation Loop nodes."""

import json
import pytest
from unittest.mock import patch

from src.graph.state import ProspectingState, SalesPlay
from src.graph.nodes.ideation import (
    divergent_ideation,
    convergent_refinement,
    _parse_plays,
    _format_competitor_proofs,
    _format_historical_plays,
)


class TestParsePlays:
    def test_parses_valid_plays(self):
        response = '''```json
[{
    "title": "AI Quality Inspection",
    "challenge": "Manual QA is slow",
    "market_standard": "Competitors use CV",
    "proposed_solution": "Deploy edge CV models",
    "business_outcome": "50% defect reduction",
    "technical_stack": ["TensorFlow", "Edge TPU"],
    "confidence_score": 0.85
}]
```'''
        plays = _parse_plays(response)
        assert len(plays) == 1
        assert plays[0]["title"] == "AI Quality Inspection"
        assert plays[0]["confidence_score"] == 0.85

    def test_handles_malformed_json(self):
        assert _parse_plays("not json") == []

    def test_handles_missing_fields(self):
        response = '[{"title": "Test"}]'
        plays = _parse_plays(response)
        assert len(plays) == 1
        assert plays[0]["challenge"] == ""


class TestFormatHelpers:
    def test_format_competitor_proofs_empty(self):
        result = _format_competitor_proofs([])
        assert "no competitor" in result.lower()

    def test_format_competitor_proofs(self, sample_competitor_proof):
        result = _format_competitor_proofs([sample_competitor_proof])
        assert "RivalCo" in result

    def test_format_historical_plays_empty(self):
        result = _format_historical_plays([])
        assert "cold start" in result.lower()

    def test_format_historical_plays(self, sample_historical_play):
        result = _format_historical_plays([sample_historical_play])
        assert "PastClient" in result


class TestDivergentIdeation:
    @patch("src.graph.nodes.ideation._call_gemini")
    def test_generates_ideas(self, mock_call, sample_state):
        mock_call.return_value = '''```json
[{
    "title": "Idea 1", "challenge": "C", "market_standard": "M",
    "proposed_solution": "S", "business_outcome": "O",
    "technical_stack": ["Python"], "confidence_score": 0.7
}]
```'''
        sample_state.client_vertical = "Tech"
        sample_state.client_domain = "SaaS"
        sample_state.deep_research_report = "Report"
        sample_state.history_synthesis = "Gaps found"

        result = divergent_ideation(sample_state)
        assert result["current_step"] == "ideas_generated"
        assert len(result["raw_ideas"]) >= 1

    @patch("src.graph.nodes.ideation._call_gemini")
    def test_ideation_failure(self, mock_call, sample_state):
        mock_call.side_effect = Exception("Failed")
        result = divergent_ideation(sample_state)
        assert "failed" in result["current_step"]


class TestConvergentRefinement:
    @patch("src.graph.nodes.ideation._call_gemini")
    def test_refines_ideas(self, mock_call, sample_state, sample_sales_play):
        mock_call.return_value = '''```json
[{
    "title": "Refined Play", "challenge": "C", "market_standard": "M",
    "proposed_solution": "S", "business_outcome": "O",
    "technical_stack": ["TF"], "confidence_score": 0.9
}]
```'''
        sample_state.raw_ideas = [sample_sales_play]
        result = convergent_refinement(sample_state)
        assert result["current_step"] == "plays_refined"
        assert len(result["refined_plays"]) >= 1

    def test_no_ideas_returns_error(self, sample_state):
        sample_state.raw_ideas = []
        result = convergent_refinement(sample_state)
        assert "failed" in result["current_step"]
