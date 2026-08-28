"""Verification Agent for Validating Real-World Effects."""
from typing import Any, Dict
from agents.base import AgentAction, BaseAgent
from security.policies.models import RiskLevel


class VerificationAgent(BaseAgent):
    """Specialist in confirming whether actions had their intended real-world effect."""
    name = "VerificationAgent"
    description = "Inspects files, process tables, exit codes, and output to verify completion."
    capabilities = ["verify_file_exists", "verify_process_running", "verify_exit_code"]
    allowed_tools = ["filesystem", "process_manager", "powershell"]
    risk_level = RiskLevel.LOW

    def plan_step(self, objective: str, context: Dict[str, Any]) -> AgentAction:
        target = context.get("target") or "output"
        return AgentAction(
            tool_name="filesystem",
            parameters={"operation": "read_file", "path": target},
            thought=f"Verifying target '{target}'.",
            expected_result="Target verified present"
        )
