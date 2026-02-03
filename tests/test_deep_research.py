"""Tests for the Deep Research node."""

import pytest
from unittest.mock import patch, MagicMock

from src.graph.state import ProspectingState
from src.graph.nodes.deep_research import (
    _extract_citations,
    _classify_vertical,
    deep_research,
)


class TestCitationExtraction:
    def test_extracts_markdown_links(self):
        text = "According to [Acme Report](https://acme.com/report) they are investing."
        citations = _extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["url"] == "https://acme.com/report"
        assert citations[0]["title"] == "Acme Report"

    def test_extracts_bare_urls(self):
        text = "See https://example.com/study for more details."
        citations = _extract_citations(text)
        assert len(citations) >= 1
        assert any("example.com" in c["url"] for c in citations)

    def test_deduplicates_urls(self):
        text = "[Report](https://acme.com/report) and also https://acme.com/report"
        citations = _extract_citations(text)
        urls = [c["url"] for c in citations]
        assert len(set(urls)) == len(urls)

    def test_empty_text_returns_empty(self):
        assert _extract_citations("") == []

    def test_no_urls_returns_empty(self):
        assert _extract_citations("Just some plain text with no links.") == []


class TestDeepResearch:
    @patch("src.graph.nodes.deep_research._get_model")
    @patch("src.graph.nodes.deep_research._call_gemini")
    def test_successful_research(self, mock_call, mock_model):
        mock_call.side_effect = [
            "Acme Corp is a leader in manufacturing. See https://acme.com",
            '```json\n{"vertical": "Manufacturing", "domain": "Discrete", "maturity_level": 3, "maturity_summary": "Developing"}\n```',
            "Gap analysis: No ML compute found.",
        ]
        mock_model.return_value = MagicMock()

        state = ProspectingState(
            client_name="Acme Corp",
            past_sales_history="Sold storage in 2023",
            base_research_prompt="Research Acme Corp",
        )
        result = deep_research(state)

        assert result["current_step"] == "research_complete"
        assert result["client_vertical"] == "Manufacturing"
        assert "Acme Corp" in result["deep_research_report"]

    @patch("src.graph.nodes.deep_research._get_model")
    @patch("src.graph.nodes.deep_research._call_gemini")
    def test_research_failure_captured(self, mock_call, mock_model):
        mock_model.side_effect = Exception("API Error")

        state = ProspectingState(client_name="Acme Corp", base_research_prompt="test")
        result = deep_research(state)

        assert "failed" in result["current_step"]
        assert any("failed" in e.lower() for e in result["errors"])
