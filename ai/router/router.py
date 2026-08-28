"""Intelligent Model Router with User Overrides."""
from typing import Optional, Tuple
from ai.gateway.gateway import ModelGateway
from config.settings import AppConfig, get_config


class ModelRouter:
    """Selects the optimal model based on task category, privacy, cost, and user overrides."""

    def __init__(self, gateway: Optional[ModelGateway] = None, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self.gateway = gateway or ModelGateway(self.config)

    def route(self, task_type: str = "general") -> Tuple[str, Optional[str]]:
        """Determine (provider_name, model_name) for a given task type."""
        models_cfg = self.config.models

        # 1. Check User Overrides
        if task_type == "coding" and models_cfg.coding_model != "auto":
            return self._resolve_model_string(models_cfg.coding_model)
        elif task_type == "reasoning" and models_cfg.reasoning_model != "auto":
            return self._resolve_model_string(models_cfg.reasoning_model)
        elif task_type == "vision" and models_cfg.vision_model != "auto":
            return self._resolve_model_string(models_cfg.vision_model)
        elif models_cfg.general_model != "auto":
            return self._resolve_model_string(models_cfg.general_model)

        # 2. Privacy Policy: If strictly prefer local or never send to cloud
        if self.config.privacy.prefer_local_models or self.config.privacy.never_send_local_files_to_cloud:
            if "ollama" in self.gateway.list_available_providers():
                return "ollama", "llama3.2:latest"
            return "offline_local", "kriti-offline-core-v1"

        # 3. Available Provider Routing
        available = self.gateway.list_available_providers()
        if "ollama" in available:
            return "ollama", "llama3.2:latest"
        elif "openai_compatible" in available:
            return "openai_compatible", models_cfg.openai_model

        # Default local offline
        return "offline_local", "kriti-offline-core-v1"

    def _resolve_model_string(self, model_str: str) -> Tuple[str, Optional[str]]:
        """Extract provider and model from strings like 'ollama/llama3.2' or 'gpt-4o'."""
        if "/" in model_str:
            parts = model_str.split("/", 1)
            return parts[0], parts[1]
        if "gpt-" in model_str or "claude-" in model_str:
            return "openai_compatible", model_str
        return "offline_local", model_str
