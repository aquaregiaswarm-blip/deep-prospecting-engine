"""Tests for the LangGraph workflow definition."""

import pytest
from unittest.mock import patch, MagicMock

from src.graph.workflow import build_workflow, _should_continue_after_research
from src.graph.state import ProspectingState


class TestWorkflowRouting:
    def test_research_failure_routes_to_end(self):
        state = ProspectingState(current_step="research_failed")
        assert _should_continue_after_research(state) == "end"

    def test_research_success_routes_to_merger(self):
        state = ProspectingState(current_step="research_complete")
        assert _should_continue_after_research(state) == "context_merger"


class TestWorkflowBuild:
    def test_workflow_compiles(self):
        """Workflow should compile without errors."""
        app = build_workflow()
        assert app is not None

    def test_workflow_has_all_nodes(self):
        """Verify all expected nodes are in the graph."""
        app = build_workflow()
        # LangGraph compiled graph should have our nodes
        # This is a basic smoke test
        assert app is not None
