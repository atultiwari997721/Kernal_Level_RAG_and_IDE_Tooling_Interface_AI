"""Base AI Model Provider Interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ModelResponse(BaseModel):
    """Normalized response from any model provider."""
    content: str
    model: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"
    usage: Optional[Dict[str, int]] = None
    latency_ms: Optional[float] = None


class BaseModelProvider(ABC):
    """Abstract interface for local and external model providers."""
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is reachable and active."""
        pass

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Generate a response synchronously or asynchronously."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """List models supported or hosted by this provider."""
        pass
