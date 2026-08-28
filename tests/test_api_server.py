"""Tests for KritiAI Desktop REST & WebSocket Server."""
from fastapi.testclient import TestClient
from apps.desktop.server import app

client = TestClient(app)


def test_api_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "power_mode" in data
    assert data["power_mode"] in ["safe", "autonomous", "risk"]
    assert "permissions" in data


def test_api_chat():
    response = client.post("/api/chat", json={"message": "Hello KritiAI"})
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert len(data["content"]) > 0


def test_api_tools():
    response = client.get("/api/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) >= 5
    tool_names = [t["name"] for t in tools]
    assert "filesystem" in tool_names
    assert "powershell" in tool_names
    assert "cmd" in tool_names
    assert "app_manager" in tool_names
    assert "system_info" in tool_names


def test_api_emergency_stop():
    # Trigger stop
    stop_resp = client.post("/api/emergency-stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "STOPPED"

    # Verify config reflects active stop
    cfg = client.get("/api/config").json()
    assert cfg["emergency_stop_active"] is True

    # Reset stop
    reset_resp = client.post("/api/emergency-stop/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "RESET"

    cfg2 = client.get("/api/config").json()
    assert cfg2["emergency_stop_active"] is False
