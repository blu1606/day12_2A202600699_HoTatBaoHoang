import os
import sys
from pathlib import Path

# Ensure root folder is in Python path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Mock environment variables before importing app
os.environ["AGENT_API_KEY"] = "test-secret-key"
os.environ["ENVIRONMENT"] = "testing"
os.environ["PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "mock-openai-key"

import pytest
from fastapi.testclient import TestClient
import app.main

@pytest.fixture
def client():
    with TestClient(app.main.app) as c:
        yield c

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ready": True}

def test_diagnose_unauthorized(client):
    response = client.post(
        "/api/v1/diagnose",
        json={"session_id": "test-session", "query": "hello"}
    )
    assert response.status_code == 401

def test_diagnose_invalid_key(client):
    response = client.post(
        "/api/v1/diagnose",
        headers={"X-API-Key": "wrong-key"},
        json={"session_id": "test-session", "query": "hello"}
    )
    assert response.status_code == 401

def test_diagnose_success(client, monkeypatch):
    # Mock the run_model_tool_loop function
    def mock_run_model_tool_loop(*args, **kwargs):
        return {
            "assistant_text": "Based on my analysis, you should review loop variables.",
            "rounds": [
                {
                    "round": 1,
                    "assistant_text": "I will think about the issue.",
                    "tool_calls": [],
                    "tool_results": []
                }
            ]
        }
    
    monkeypatch.setattr(app.main, "run_model_tool_loop", mock_run_model_tool_loop)
    
    response = client.post(
        "/api/v1/diagnose",
        headers={"X-API-Key": "test-secret-key"},
        json={
            "session_id": "test-session",
            "query": "What is wrong with my code?",
            "history": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "steps" in data
    assert "task_id" in data
    assert data["summary"] == "Based on my analysis, you should review loop variables."

