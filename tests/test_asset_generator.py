"""Tests for the Asset Generator node."""

import pytest
from unittest.mock import patch
from pathlib import Path

from src.graph.nodes.asset_generator import asset_generator, _format_proofs, _save_markdown


class TestFormatProofs:
    def test_empty_proofs(self):
        result = _format_proofs([])
        assert "no competitor" in result.lower()

    def test_formats_proofs(self, sample_competitor_proof):
        result = _format_proofs([sample_competitor_proof])
        assert "RivalCo" in result
        assert "Predictive maintenance" in result


class TestSaveMarkdown:
    def test_creates_file(self, tmp_path):
        filepath = _save_markdown(str(tmp_path), "test.md", "# Test Content")
        assert Path(filepath).exists()
        assert Path(filepath).read_text() == "# Test Content"

    def test_creates_directory(self, tmp_path):
        output_dir = str(tmp_path / "nested" / "dir")
        filepath = _save_markdown(output_dir, "test.md", "content")
        assert Path(filepath).exists()


class TestAssetGenerator:
    @patch("src.graph.nodes.asset_generator._call_gemini")
    def test_generates_assets(self, mock_call, researched_state):
        mock_call.side_effect = [
            "# One Pager\n\nGreat content here.",
            "# Strategic Plan\n\nComprehensive plan.",
        ]
        result = asset_generator(researched_state)

        assert result["current_step"] == "assets_generated"
        assert len(result["one_pagers"]) == 1
        assert result["strategic_plan"]

    def test_no_plays_returns_error(self, sample_state):
        sample_state.refined_plays = []
        result = asset_generator(sample_state)
        assert "failed" in result["current_step"]

    @patch("src.graph.nodes.asset_generator._call_gemini")
    def test_failure_captured(self, mock_call, researched_state):
        mock_call.side_effect = Exception("API Error")
        result = asset_generator(researched_state)
        assert "failed" in result["current_step"]
        assert any("failed" in e.lower() for e in result["errors"])
