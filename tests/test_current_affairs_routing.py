"""Tests for Current Affairs Dynamic Routing (Qwen/DeepSeek) & Qwen 7B Default for Chat."""
from fastapi.testclient import TestClient
from ai.router.router import ModelRouter
from apps.desktop.server import app, model_router, model_gateway


def test_is_current_affairs_query_detection():
    # True positives
    assert ModelRouter.is_current_affairs_query("What are the latest topics in current affairs?") is True
    assert ModelRouter.is_current_affairs_query("Give me today's news and breaking updates") is True
    assert ModelRouter.is_current_affairs_query("Who is the current prime minister of India?") is True
    assert ModelRouter.is_current_affairs_query("What are the latest developments in AI in 2026?") is True
    assert ModelRouter.is_current_affairs_query("Tell me about the recent election results") is True

    # True negatives
    assert ModelRouter.is_current_affairs_query("Write a python script to reverse a linked list") is False
    assert ModelRouter.is_current_affairs_query("Create a calculator in K:\\calc") is False
    assert ModelRouter.is_current_affairs_query("How does photosynthesis work?") is False


def test_route_current_affairs_selects_qwen_or_deepseek():
    prov, model = model_router.route_current_affairs("What is happening in current affairs today?")
    assert "qwen" in model.lower() or "deepseek" in model.lower()


def test_route_chat_default_selects_qwen():
    prov, model = model_router.route_chat_default()
    assert "qwen" in model.lower()


def test_api_models_endpoint_has_qwen_default_chat_model():
    client = TestClient(app)
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.json()

    assert "default_chat_model" in data
    assert "qwen" in data["default_chat_model"].lower()


def test_chat_auto_switches_for_current_affairs():
    client = TestClient(app)
    res = client.post(
        "/api/chat",
        json={"message": "What are the latest breaking news and current affairs today?"}
    )
    assert res.status_code == 200
    data = res.json()

    assert data["switched_model"] is True
    assert "Current Affairs" in data["switch_reason"]
    assert "qwen" in data["model"].lower() or "deepseek" in data["model"].lower()


def test_chat_uses_default_qwen_for_normal_message():
    client = TestClient(app)
    res = client.post(
        "/api/chat",
        json={"message": "Hello, explain how binary search works."}
    )
    assert res.status_code == 200
    data = res.json()

    # Model used should be the default Qwen model
    assert "qwen" in data["model"].lower()
    assert data["switched_model"] is False
