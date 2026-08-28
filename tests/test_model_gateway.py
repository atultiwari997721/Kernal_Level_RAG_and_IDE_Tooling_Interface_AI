"""Tests for KritiAI Model Gateway and Router."""
from ai.gateway.gateway import ModelGateway
from ai.router.router import ModelRouter
from config.settings import AppConfig, ModelSelection


def test_offline_intelligence_provider():
    gateway = ModelGateway()
    resp = gateway.generate(
        messages=[{"role": "user", "content": "Create a folder called TestProject"}]
    )
    assert resp.content != ""
    assert resp.tool_calls is not None
    assert len(resp.tool_calls) > 0
    call = resp.tool_calls[0]
    assert call["function"]["name"] == "filesystem"
    assert call["function"]["arguments"]["operation"] == "create_folder"


def test_model_router_offline_preference():
    config = AppConfig()
    gateway = ModelGateway(config)
    router = ModelRouter(gateway, config)

    provider, model = router.route(task_type="general")
    assert provider == "offline_local"
    assert "kriti" in model.lower()


def test_model_router_user_override():
    config = AppConfig(models=ModelSelection(general_model="my-custom-model", coding_model="auto"))
    gateway = ModelGateway(config)
    router = ModelRouter(gateway, config)

    provider, model = router.route(task_type="general")
    assert model == "my-custom-model"
