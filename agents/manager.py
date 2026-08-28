"""Agent Manager and Dispatcher for KritiAI."""
from typing import Any, Dict, List, Optional
from agents.base import BaseAgent
from agents.coding import CodingAgent
from agents.filesystem import FileSystemAgent
from agents.verification import VerificationAgent
from agents.windows import WindowsAgent


class AgentManager:
    """Dispatches tasks to the appropriate specialized agent."""

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        defaults = [
            FileSystemAgent(),
            WindowsAgent(),
            CodingAgent(),
            VerificationAgent(),
        ]
        for a in defaults:
            self.register_agent(a)

    def register_agent(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._agents.values()]

    def select_agent_for_goal(self, goal: str) -> BaseAgent:
        """Heuristic and intent-based selection of the best agent."""
        g_lower = goal.lower()
        if any(w in g_lower for w in ["folder", "dir", "file", "read", "write", "mkdir"]):
            return self._agents.get("FileSystemAgent", FileSystemAgent())
        elif any(w in g_lower for w in ["notepad", "app", "window", "hardware", "system info", "calc", "screen"]):
            return self._agents.get("WindowsAgent", WindowsAgent())
        elif any(w in g_lower for w in ["pip", "npm", "build", "test", "git", "run", "python", "compile"]):
            return self._agents.get("CodingAgent", CodingAgent())
        return self._agents.get("FileSystemAgent", FileSystemAgent())
