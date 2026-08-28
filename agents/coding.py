"""Coding and Terminal Specialist Agent for KritiAI."""
from typing import Any, Dict
from agents.base import AgentAction, BaseAgent
from security.policies.models import RiskLevel


class CodingAgent(BaseAgent):
    """Specialized agent for running dev commands, installing dependencies, builds, and tests."""
    name = "CodingAgent"
    description = "Executes development workflows, terminal commands, builds, and test suites."
    capabilities = ["run_command", "install_dependencies", "run_tests", "git_operations"]
    allowed_tools = ["powershell", "cmd", "filesystem"]
    risk_level = RiskLevel.MEDIUM

    def plan_step(self, objective: str, context: Dict[str, Any]) -> AgentAction:
        cmd = context.get("command") or objective
        cwd = context.get("working_directory")
        shell = context.get("shell", "powershell")

        return AgentAction(
            tool_name=shell,
            parameters={"command": cmd, "working_directory": cwd},
            thought=f"Executing terminal command: {cmd}",
            expected_result="Command completed with exit code 0"
        )
