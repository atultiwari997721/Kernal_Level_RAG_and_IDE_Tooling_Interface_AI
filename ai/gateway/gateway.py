"""Central Model Gateway for KritiAI with Dynamic Model Discovery."""
from typing import Any, Dict, List, Optional
from ai.providers.base import BaseModelProvider, ModelResponse
from ai.providers.offline_provider import OfflineIntelligenceProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAICompatibleProvider
from config.settings import AppConfig, get_config


class ModelGateway:
    """Provider-independent interface for AI model inference and discovery."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self._providers: Dict[str, BaseModelProvider] = {}
        self._setup_providers()

    def _setup_providers(self) -> None:
        # 1. Always enable local offline provider
        self.register_provider(OfflineIntelligenceProvider())

        # 2. Local Ollama provider
        if self.config.models.ollama_endpoint:
            self.register_provider(OllamaProvider(endpoint=self.config.models.ollama_endpoint))

        # 3. External API provider if configured
        if self.config.models.openai_api_key or self.config.models.openai_base_url:
            self.register_provider(
                OpenAICompatibleProvider(
                    api_key=self.config.models.openai_api_key,
                    base_url=self.config.models.openai_base_url,
                    default_model=self.config.models.openai_model
                )
            )

    def register_provider(self, provider: BaseModelProvider) -> None:
        self._providers[provider.name] = provider

    def refresh_providers(self, config: Optional[AppConfig] = None) -> None:
        if config:
            self.config = config
        self._providers.clear()
        self._setup_providers()

    def get_provider(self, name: str) -> Optional[BaseModelProvider]:
        return self._providers.get(name)

    def list_available_providers(self) -> List[str]:
        return [name for name, prov in self._providers.items() if prov.is_available()]

    def list_all_models(self) -> List[Dict[str, Any]]:
        """Discover and return all available downloaded and API models."""
        models: List[Dict[str, Any]] = []

        # 1. Check local Ollama models
        if "ollama" in self._providers and self._providers["ollama"].is_available():
            ollama_prov = self._providers["ollama"]
            for m in ollama_prov.list_models():
                models.append({
                    "id": f"ollama:{m}",
                    "name": m,
                    "provider": "ollama",
                    "provider_display": "Local (Ollama)",
                    "type": "local",
                    "is_local": True,
                    "description": "Downloaded local model running via Ollama"
                })

        # 2. Built-in Offline Intelligence models
        if "offline_local" in self._providers:
            offline_prov = self._providers["offline_local"]
            for m in offline_prov.list_models():
                models.append({
                    "id": f"offline_local:{m}",
                    "name": m,
                    "provider": "offline_local",
                    "provider_display": "Built-in Offline",
                    "type": "local",
                    "is_local": True,
                    "description": "Local rule-and-intent offline intelligence"
                })

        # 3. External API models if configured
        if "openai_compatible" in self._providers and self._providers["openai_compatible"].is_available():
            api_prov = self._providers["openai_compatible"]
            for m in api_prov.list_models():
                models.append({
                    "id": f"openai_compatible:{m}",
                    "name": m,
                    "provider": "openai_compatible",
                    "provider_display": "External API",
                    "type": "cloud",
                    "is_local": False,
                    "description": "External API model"
                })

        return models

    def generate(
        self,
        messages: List[Dict[str, str]],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7
    ) -> ModelResponse:
        # Check if composite model ID passed (e.g. "ollama:kritiai:latest")
        if model and ":" in model:
            parts = model.split(":", 1)
            if parts[0] in self._providers:
                provider_name = parts[0]
                model = parts[1]

        # Determine provider
        if provider_name and provider_name in self._providers:
            prov = self._providers[provider_name]
        else:
            # Check local Ollama first if prefer_local is true and Ollama is running
            if self.config.models.prefer_local and "ollama" in self._providers and self._providers["ollama"].is_available():
                prov = self._providers["ollama"]
            # Next check OpenAI if configured and available
            elif "openai_compatible" in self._providers and self._providers["openai_compatible"].is_available():
                prov = self._providers["openai_compatible"]
            # Default to offline local intelligence
            else:
                prov = self._providers.get("offline_local", OfflineIntelligenceProvider())

        return prov.generate(messages=messages, model=model, tools=tools, temperature=temperature)
