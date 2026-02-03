"""Tests for the Competitor Scout node."""

import pytest
from unittest.mock import patch

from src.graph.state import ProspectingState
from src.graph.nodes.competitor_scout import competitor_scout, _parse_competitors


class TestParseCompetitors:
    def test_parses_valid_json(self):
        response = '''```json
[{"competitor_name": "RivalCo", "use_case": "Predictive maintenance", "outcome": "30% less downtime", "source_title": "Case Study", "source_url": "https://rival.com/case"}]
```'''
        proofs = _parse_competitors(response)
        assert len(proofs) == 1
        assert proofs[0]["competitor_name"] == "RivalCo"
        assert proofs[0]["source"]["url"] == "https://rival.com/case"

    def test_handles_malformed_json(self):
        proofs = _parse_competitors("This is not JSON at all")
        assert proofs == []

    def test_handles_empty_array(self):
        proofs = _parse_competitors("[]")
        assert proofs == []

    def test_parses_multiple_competitors(self):
        response = '''```json
[
    {"competitor_name": "A", "use_case": "ML", "outcome": "good", "source_title": "", "source_url": ""},
    {"competitor_name": "B", "use_case": "CV", "outcome": "great", "source_title": "", "source_url": ""}
]
```'''
        proofs = _parse_competitors(response)
        assert len(proofs) == 2


class TestCompetitorScout:
    @patch("src.graph.nodes.competitor_scout._call_gemini")
    def test_successful_scouting(self, mock_call):
        mock_call.return_value = '''```json
[{"competitor_name": "TechCo", "use_case": "AI QA", "outcome": "50% faster", "source_title": "Blog", "source_url": "https://techco.com"}]
```'''
        state = ProspectingState(
            client_name="Acme",
            client_vertical="Manufacturing",
            deep_research_report="Acme is in manufacturing...",
        )
        result = competitor_scout(state)

        assert result["current_step"] == "competitors_scouted"
        assert len(result["competitor_proofs"]) == 1

    @patch("src.graph.nodes.competitor_scout._call_gemini")
    def test_scouting_failure(self, mock_call):
        mock_call.side_effect = Exception("API down")

        state = ProspectingState(
            client_name="Acme",
            client_vertical="Manufacturing",
            deep_research_report="report",
        )
        result = competitor_scout(state)

        assert "failed" in result["current_step"]
