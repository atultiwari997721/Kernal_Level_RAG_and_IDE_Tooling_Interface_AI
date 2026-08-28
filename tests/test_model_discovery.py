"""Tests for Dynamic Model Discovery, Multi-Provider API Integration, and Chat Model Selection."""
from fastapi.testclient import TestClient
from ai.gateway.gateway import ModelGateway
from apps.desktop.server import app
from config.settings import AppConfig


def test_model_gateway_list_all_models():
    gateway = ModelGateway()
    all_models = gateway.list_all_models()

    assert len(all_models) > 0
    # Must at least include built-in offline models
    offline_models = [m for m in all_models if m["provider"] == "offline_local"]
    assert len(offline_models) > 0
    assert any(m["name"] == "kriti-offline-core-v1" for m in offline_models)
    assert offline_models[0]["is_local"] is True


def test_api_get_models():
    client = TestClient(app)
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.json()

    assert "models" in data
    assert "active_model" in data
    assert len(data["models"]) > 0


def test_api_chat_with_explicit_model_selection():
    client = TestClient(app)
    # Chat specifying explicit model
    res = client.post(
        "/api/chat",
        json={
            "message": "Hello from custom model test",
            "model": "offline_local:kriti-offline-core-v1"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "offline_local" in data["model"]
    assert "Hello" in data["content"] or "KritiAI" in data["content"]


def test_api_configure_provider():
    client = TestClient(app)
    res = client.post(
        "/api/models/providers",
        json={
            "provider": "openai_compatible",
            "base_url": "https://api.openai.com/v1",
            "api_key": "test-key-mock",
            "default_model": "gpt-4o"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "models" in data
