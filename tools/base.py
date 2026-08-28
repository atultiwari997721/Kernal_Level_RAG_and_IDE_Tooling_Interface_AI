"""Standardized Base Tool Definition for KritiAI."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
from security.policies.models import RiskLevel


class ToolResult(BaseModel):
    """Structured tool execution output."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None


class BaseTool(ABC):
    """Abstract base class for all KritiAI tools."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    risk_level: RiskLevel = RiskLevel.MEDIUM
    required_permission: Optional[str] = None
    timeout_seconds: int = 60

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool action with given parameters."""
        pass

    @abstractmethod
    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        """Independently verify whether the real-world action had its intended effect."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "risk_level": self.risk_level.value,
            "required_permission": self.required_permission,
            "timeout_seconds": self.timeout_seconds,
        }
