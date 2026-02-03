"""Tests for ChromaDB memory operations."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.memory.chroma_query import query_similar_verticals, query_similar_plays
from src.memory.chroma_store import store_plays, store_client_profile
from src.graph.state import ProspectingState, SalesPlay


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB tests."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestChromaQuery:
    def test_cold_start_verticals(self, temp_chroma_dir):
        """Empty DB should return empty list, not error."""
        result = query_similar_verticals(temp_chroma_dir, "Healthcare", "Pharma")
        assert result == []

    def test_cold_start_plays(self, temp_chroma_dir):
        """Empty DB should return empty list, not error."""
        result = query_similar_plays(temp_chroma_dir, "Healthcare", "Some research")
        assert result == []


class TestChromaStore:
    def test_store_plays(self, temp_chroma_dir, researched_state):
        """Should store plays without error."""
        count = store_plays(temp_chroma_dir, researched_state)
        assert count == len(researched_state.refined_plays)

    def test_store_no_plays(self, temp_chroma_dir, sample_state):
        """Should handle empty plays gracefully."""
        sample_state.refined_plays = []
        count = store_plays(temp_chroma_dir, sample_state)
        assert count == 0

    def test_store_client_profile(self, temp_chroma_dir, researched_state):
        """Should store profile without error."""
        result = store_client_profile(temp_chroma_dir, researched_state)
        assert result is True

    def test_roundtrip(self, temp_chroma_dir, researched_state):
        """Store plays, then query them back."""
        store_plays(temp_chroma_dir, researched_state)
        store_client_profile(temp_chroma_dir, researched_state)

        # Query back
        verticals = query_similar_verticals(
            temp_chroma_dir,
            researched_state.client_vertical,
            researched_state.client_domain,
        )
        plays = query_similar_plays(
            temp_chroma_dir,
            researched_state.client_vertical,
            "manufacturing quality inspection",
        )

        # Should find at least what we stored
        assert len(verticals) >= 1
        assert len(plays) >= 1
