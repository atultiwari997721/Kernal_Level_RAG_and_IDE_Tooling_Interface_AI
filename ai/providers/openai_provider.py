"""Generic OpenAI-Compatible Model Provider for Cloud and Local Endpoints."""
import time
from typing import Any, Dict, List, Optional
import httpx
from ai.providers.base import BaseModelProvider, ModelResponse


class OpenAICompatibleProvider(BaseModelProvider):
    """Adapter for OpenAI, OpenRouter, Groq, LM Studio, or vLLM."""
    name = "openai_compatible"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o-mini"
    ):
        self.api_key = api_key or ""
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.default_model = default_model
        self._cached_models: Optional[List[str]] = None
        self._models_cache_time: float = 0.0

    def is_available(self) -> bool:
        return bool(self.api_key or "localhost" in self.base_url or "127.0.0.1" in self.base_url)

    def list_models(self) -> List[str]:
        if not self.is_available():
            return []
        now = time.time()
        if self._cached_models is not None and (now - self._models_cache_time) < 60.0:
            return self._cached_models
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/models", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    self._cached_models = [m["id"] for m in data.get("data", [])]
                    self._models_cache_time = now
                    return self._cached_models
        except Exception:
            pass
        self._cached_models = [self.default_model]
        self._models_cache_time = now
        return self._cached_models

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        start_t = time.time()
        chosen_model = model or self.default_model
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                choice = data["choices"][0]
                msg = choice.get("message", {})
                latency = round((time.time() - start_t) * 1000, 2)
                return ModelResponse(
                    content=msg.get("content", ""),
                    model=chosen_model,
                    tool_calls=msg.get("tool_calls"),
                    finish_reason=choice.get("finish_reason", "stop"),
                    latency_ms=latency
                )
        except Exception as ex:
            latency = round((time.time() - start_t) * 1000, 2)
            return ModelResponse(
                content=f"[API Connection Error: {str(ex)}]",
                model=chosen_model,
                latency_ms=latency
            )
