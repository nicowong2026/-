"""
tests/test_api.py
API endpoint tests using FastAPI TestClient.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_video_returns_task_id():
    resp = client.post(
        "/v1/videos",
        json={
            "prompt": "A panda in bamboo forest",
            "duration": 10,
            "style": "cinematic",
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_get_task_status_not_found():
    resp = client.get("/v1/videos/nonexistent-task-id")
    assert resp.status_code == 404


def test_get_task_status_found():
    # Submit a task first
    post_resp = client.post(
        "/v1/videos",
        json={"prompt": "Sunset over mountains", "duration": 5},
    )
    task_id = post_resp.json()["task_id"]

    # Poll status
    get_resp = client.get(f"/v1/videos/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["task_id"] == task_id
