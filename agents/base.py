"""Specialized Agent Base Interface for KritiAI."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from security.policies.models import RiskLevel


class AgentAction(BaseModel):
    """Action proposed by an agent."""
    tool_name: str
    parameters: Dict[str, Any]
    thought: str
    expected_result: Optional[str] = None


class BaseAgent(ABC):
    """Base class for specialized autonomous agents."""
    name: str
    description: str
    capabilities: List[str]
    allowed_tools: List[str]
    risk_level: RiskLevel = RiskLevel.MEDIUM

    @abstractmethod
    def plan_step(self, objective: str, context: Dict[str, Any]) -> AgentAction:
        """Decide next tool action for a given sub-objective."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "allowed_tools": self.allowed_tools,
            "risk_level": self.risk_level.value
        }
