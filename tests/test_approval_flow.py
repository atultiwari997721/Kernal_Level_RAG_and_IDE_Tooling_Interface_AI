"""Tests for the Approval Modal and Task Resumption API."""
from fastapi.testclient import TestClient
from apps.desktop.server import app, orchestrator
from config.settings import PowerMode


def test_approval_flow_allow_once():
    client = TestClient(app)
    # Execute a goal in SAFE power mode so it requires approval
    res = client.post(
        "/api/kritimode/execute",
        json={
            "goal": "create folder TestApprovalFolder",
            "power_mode": "safe"
        }
    )
    assert res.status_code == 200
    data = res.json()

    # In safe mode, state-altering operations require approval
    assert data["approval_required"] is True
    assert "task_id" in data
    task_id = data["task_id"]

    # Approve the task
    approve_res = client.post(
        f"/api/tasks/{task_id}/approve",
        json={
            "decision": "allow_once",
            "tool_name": data.get("tool_name"),
            "action": data.get("action")
        }
    )
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["success"] is True
    assert approve_data["status"] == "completed"


def test_approval_flow_deny():
    client = TestClient(app)
    # Execute a goal in SAFE power mode
    res = client.post(
        "/api/kritimode/execute",
        json={
            "goal": "create folder TestDenyFolder",
            "power_mode": "safe"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["approval_required"] is True
    task_id = data["task_id"]

    # Deny the task
    deny_res = client.post(
        f"/api/tasks/{task_id}/approve",
        json={
            "decision": "deny"
        }
    )
    assert deny_res.status_code == 200
    deny_data = deny_res.json()
    assert deny_data["success"] is False
    assert deny_data["status"] == "cancelled"
