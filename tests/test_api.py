"""Tests for the FastAPI API layer."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.run_store import RunStore, run_store
from src.api.models import RunStatus
from src.graph.state import ProspectingState


@pytest.fixture(autouse=True)
def fresh_store(monkeypatch):
    """Replace the global run_store with a fresh one for each test."""
    fresh = RunStore()
    monkeypatch.setattr("src.api.main.run_store", fresh)
    monkeypatch.setattr("src.api.run_store.run_store", fresh)
    return fresh


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "deep-prospecting-engine"
        assert "version" in data

    def test_health_schema(self, client):
        resp = client.get("/api/health")
        data = resp.json()
        assert set(data.keys()) == {"status", "version", "service"}


class TestProspectEndpoint:
    @patch("src.api.main._run_pipeline")
    def test_start_prospect_returns_202(self, mock_pipeline, client):
        resp = client.post("/api/prospect", json={
            "client_name": "Acme Corp",
            "past_sales_history": "Sold stuff",
            "base_research_prompt": "",
        })
        assert resp.status_code == 202
        data = resp.json()
        assert data["client_name"] == "Acme Corp"
        assert data["status"] == "pending"
        assert "run_id" in data
        assert "created_at" in data

    @patch("src.api.main._run_pipeline")
    def test_start_prospect_requires_client_name(self, mock_pipeline, client):
        resp = client.post("/api/prospect", json={
            "past_sales_history": "Sold stuff",
        })
        assert resp.status_code == 422  # validation error

    @patch("src.api.main._run_pipeline")
    def test_start_prospect_empty_client_name_rejected(self, mock_pipeline, client):
        resp = client.post("/api/prospect", json={
            "client_name": "",
        })
        assert resp.status_code == 422

    @patch("src.api.main._run_pipeline")
    def test_start_prospect_defaults(self, mock_pipeline, client):
        resp = client.post("/api/prospect", json={
            "client_name": "TestCo",
        })
        assert resp.status_code == 202
        data = resp.json()
        assert data["client_name"] == "TestCo"


class TestRunStatusEndpoint:
    @patch("src.api.main._run_pipeline")
    def test_get_status_of_existing_run(self, mock_pipeline, client, fresh_store):
        # Create a run
        run_id = fresh_store.create_run("TestCo", "", "")
        resp = client.get(f"/api/prospect/{run_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == run_id
        assert data["client_name"] == "TestCo"
        assert data["status"] == "pending"

    def test_get_status_nonexistent_run(self, client):
        resp = client.get("/api/prospect/nonexistent123/status")
        assert resp.status_code == 404

    @patch("src.api.main._run_pipeline")
    def test_completed_run_has_results(self, mock_pipeline, client, fresh_store):
        run_id = fresh_store.create_run("TestCo", "", "")
        state = ProspectingState(
            client_name="TestCo",
            client_vertical="Manufacturing",
            client_domain="Discrete",
            refined_plays=[{
                "title": "AI Play",
                "challenge": "x",
                "market_standard": "y",
                "proposed_solution": "z",
                "business_outcome": "w",
                "technical_stack": ["TF"],
                "confidence_score": 0.9,
                "citations": [],
            }],
            one_pagers={"AI Play": "# Content"},
        )
        fresh_store.complete_run(run_id, state)

        resp = client.get(f"/api/prospect/{run_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["plays_count"] == 1
        assert data["client_vertical"] == "Manufacturing"
        assert len(data["refined_plays"]) == 1
        assert data["one_pagers"]["AI Play"] == "# Content"


class TestListRunsEndpoint:
    def test_empty_list(self, client):
        resp = client.get("/api/runs")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("src.api.main._run_pipeline")
    def test_list_after_creating_runs(self, mock_pipeline, client, fresh_store):
        fresh_store.create_run("ClientA", "", "")
        fresh_store.create_run("ClientB", "", "")

        resp = client.get("/api/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Most recent first
        assert data[0]["client_name"] == "ClientB"
        assert data[1]["client_name"] == "ClientA"


class TestStreamEndpoint:
    def test_stream_nonexistent_run(self, client):
        resp = client.get("/api/prospect/nonexistent/stream")
        assert resp.status_code == 404

    @patch("src.api.main._run_pipeline")
    def test_stream_completed_run_returns_immediately(self, mock_pipeline, client, fresh_store):
        run_id = fresh_store.create_run("TestCo", "", "")
        state = ProspectingState(client_name="TestCo")
        fresh_store.complete_run(run_id, state)

        resp = client.get(f"/api/prospect/{run_id}/stream")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]


class TestRunStore:
    def test_create_and_get(self, fresh_store):
        run_id = fresh_store.create_run("TestCo", "history", "prompt")
        run = fresh_store.get_run(run_id)
        assert run is not None
        assert run["client_name"] == "TestCo"
        assert run["status"] == RunStatus.PENDING

    def test_update_step(self, fresh_store):
        run_id = fresh_store.create_run("TestCo", "", "")
        fresh_store.update_step(run_id, "deep_research", RunStatus.RUNNING)
        run = fresh_store.get_run(run_id)
        assert run["current_step"] == "deep_research"
        assert run["status"] == RunStatus.RUNNING

    def test_fail_run(self, fresh_store):
        run_id = fresh_store.create_run("TestCo", "", "")
        fresh_store.fail_run(run_id, "Something broke")
        run = fresh_store.get_run(run_id)
        assert run["status"] == RunStatus.FAILED
        assert run["error"] == "Something broke"

    def test_list_ordering(self, fresh_store):
        import time
        fresh_store.create_run("First", "", "")
        time.sleep(0.01)
        fresh_store.create_run("Second", "", "")
        runs = fresh_store.list_runs()
        assert runs[0].client_name == "Second"
        assert runs[1].client_name == "First"

    def test_get_nonexistent(self, fresh_store):
        assert fresh_store.get_run("nope") is None
        assert fresh_store.get_detail("nope") is None
