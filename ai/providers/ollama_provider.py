"""Local Ollama Provider Adapter for KritiAI."""
import time
from typing import Any, Dict, List, Optional
import httpx
from ai.providers.base import BaseModelProvider, ModelResponse


class OllamaProvider(BaseModelProvider):
    """Adapter for local Ollama LLM server."""
    name = "ollama"

    def __init__(self, endpoint: str = "http://localhost:11434"):
        self.endpoint = endpoint.rstrip("/")

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.endpoint}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.endpoint}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        start_t = time.time()
        available_models = self.list_models()
        chosen_model = model or (available_models[0] if available_models else "kriti-offline-core-v1")
        payload = {
            "model": chosen_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                res = client.post(f"{self.endpoint}/api/chat", json=payload)
                res.raise_for_status()
                data = res.json()
                msg = data.get("message", {})
                latency = round((time.time() - start_t) * 1000, 2)
                return ModelResponse(
                    content=msg.get("content", ""),
                    model=chosen_model,
                    latency_ms=latency
                )
        except Exception:
            # Graceful local offline fallback
            from ai.providers.offline_provider import OfflineIntelligenceProvider
            offline_prov = OfflineIntelligenceProvider()
            return offline_prov.generate(messages=messages, model="offline_fallback", tools=tools)
