"""Tests for the Input Processor node."""

import pytest
from src.graph.state import ProspectingState
from src.graph.nodes.input_processor import input_processor


class TestInputProcessor:
    def test_valid_input(self, sample_state):
        result = input_processor(sample_state)
        assert result["current_step"] == "input_processed"
        assert not result["errors"]
        assert result["base_research_prompt"]

    def test_empty_client_name_produces_error(self):
        state = ProspectingState(client_name="", past_sales_history="some history")
        result = input_processor(state)
        assert any("required" in e.lower() for e in result["errors"])

    def test_whitespace_client_name_produces_error(self):
        state = ProspectingState(client_name="   ", past_sales_history="history")
        result = input_processor(state)
        assert any("required" in e.lower() for e in result["errors"])

    def test_missing_sales_history_still_proceeds(self):
        state = ProspectingState(client_name="Test Corp", past_sales_history="")
        result = input_processor(state)
        assert result["current_step"] == "input_processed"

    def test_custom_prompt_preserved(self):
        state = ProspectingState(
            client_name="Test Corp",
            base_research_prompt="Focus on supply chain for {client_name}",
        )
        result = input_processor(state)
        assert "Test Corp" in result["base_research_prompt"]
        assert "supply chain" in result["base_research_prompt"]

    def test_default_prompt_includes_client_name(self, sample_state):
        sample_state.base_research_prompt = ""
        result = input_processor(sample_state)
        assert sample_state.client_name in result["base_research_prompt"]
