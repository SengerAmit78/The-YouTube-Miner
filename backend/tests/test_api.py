"""
Integration tests for FastAPI backend endpoints using TestClient and pytest.
These tests provide coverage for /run, /status, /result, and related endpoints
without actually running pipeline jobs or downloading files (all core pipeline steps are mocked).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
import json

from backend.main import app

client = TestClient(app)

DUMMY_RUN_STATE = {
    "step": "done",
    "error": None,
    "result": {
        "run_id": "run_123456",
        "output_dir": "output/run_123456",
        "webm_url": None,
        "wav_url": None,
        "caption_url": None,
        "chunkFiles": ["/output/run_123456/chunks/chunk_001.wav"]
    }
}

def fake_pipeline(*a, **k):
    return DUMMY_RUN_STATE["result"]

def fake_background_run(args, runid):
    pass

@patch("backend.services.run_manager.background_run", side_effect=fake_background_run)
def test_run_and_status(mock_bg):
    response = client.post("/run", json={
        "youtube_url": "https://youtu.be/testvideo",
        "language": "en",
        "model_size": "tiny"
    })
    assert response.status_code in (200, 202)
    run_id = response.json()["run_id"]
    status_resp = client.get(f"/status/{run_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["run_id"] == run_id
    assert "step" in status_data

@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(DUMMY_RUN_STATE))
@patch("os.path.exists", return_value=True)
def test_get_result_endpoint(mock_exists, mock_file):
    run_id = "run_123456"
    resp = client.get(f"/result/{run_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert "chunkFiles" in data

@patch("backend.services.run_manager.get_run_result", return_value=None)
def test_get_result_endpoint_404(mock_res):
    resp = client.get("/result/missingid")
    assert resp.status_code == 404
    assert "unavailable" in resp.text.lower() or "not found" in resp.text.lower()
