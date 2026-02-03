"""Tests for the Context Merger node."""

import pytest
from unittest.mock import patch

from src.graph.state import ProspectingState
from src.graph.nodes.context_merger import context_merger


class TestContextMerger:
    @patch("src.graph.nodes.context_merger.query_similar_plays")
    @patch("src.graph.nodes.context_merger.query_similar_verticals")
    def test_merges_context(self, mock_verticals, mock_plays):
        mock_verticals.return_value = []
        mock_plays.return_value = []

        state = ProspectingState(
            client_name="Test Corp",
            client_vertical="Healthcare",
            client_domain="Pharma",
            deep_research_report="Test report content",
        )
        result = context_merger(state)

        assert result["current_step"] == "context_merged"
        assert isinstance(result["similar_verticals"], list)
        assert isinstance(result["similar_plays"], list)

    @patch("src.graph.nodes.context_merger.query_similar_plays")
    @patch("src.graph.nodes.context_merger.query_similar_verticals")
    def test_cold_start_returns_empty(self, mock_verticals, mock_plays):
        """On first run with empty ChromaDB, should return empty lists gracefully."""
        mock_verticals.return_value = []
        mock_plays.return_value = []

        state = ProspectingState(
            client_name="New Client",
            client_vertical="Fintech",
            client_domain="Payments",
            deep_research_report="First ever report",
        )
        result = context_merger(state)

        assert result["similar_verticals"] == []
        assert result["similar_plays"] == []
        assert result["current_step"] == "context_merged"

    @patch("src.graph.nodes.context_merger.query_similar_plays")
    @patch("src.graph.nodes.context_merger.query_similar_verticals")
    def test_returns_historical_data(self, mock_verticals, mock_plays, sample_historical_play):
        mock_verticals.return_value = [sample_historical_play]
        mock_plays.return_value = [sample_historical_play]

        state = ProspectingState(
            client_name="Test Corp",
            client_vertical="Manufacturing",
            client_domain="Discrete",
            deep_research_report="Report",
        )
        result = context_merger(state)

        assert len(result["similar_verticals"]) == 1
        assert len(result["similar_plays"]) == 1
        assert result["similar_verticals"][0]["client_name"] == "PastClient Inc"
