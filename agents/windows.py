"""Windows Automation Agent for KritiAI."""
from typing import Any, Dict
from agents.base import AgentAction, BaseAgent
from security.policies.models import RiskLevel


class WindowsAgent(BaseAgent):
    """Specialized agent for Windows application control, processes, and system telemetry."""
    name = "WindowsAgent"
    description = "Manages Windows desktop applications, processes, clipboard, and hardware inspection."
    capabilities = ["launch_app", "close_app", "inspect_process", "system_info", "ui_action"]
    allowed_tools = ["app_manager", "process_manager", "system_info", "clipboard", "ui_automation", "screenshot"]
    risk_level = RiskLevel.MEDIUM

    def plan_step(self, objective: str, context: Dict[str, Any]) -> AgentAction:
        obj_lower = objective.lower()
        if "hardware" in obj_lower or "system" in obj_lower:
            return AgentAction(
                tool_name="system_info",
                parameters={"detailed": True},
                thought="Checking Windows hardware parameters and RAM limits.",
                expected_result="Hardware telemetry collected"
            )
        elif "open" in obj_lower or "launch" in obj_lower:
            app = context.get("app_name") or "notepad"
            return AgentAction(
                tool_name="app_manager",
                parameters={"action": "launch", "app_name": app},
                thought=f"Launching application '{app}'.",
                expected_result=f"Application '{app}' running"
            )
        else:
            return AgentAction(
                tool_name="process_manager",
                parameters={"action": "list", "limit": 20},
                thought="Inspecting active Windows processes.",
                expected_result="Process list returned"
            )
