"""Self-Correction and Failure Recovery Engine for KritiAI."""
from typing import Any, Dict, Optional
from pydantic import BaseModel


class RecoveryPlan(BaseModel):
    """Diagnosed failure cause and proposed remediation."""
    cause: str
    action: str  # "retry", "alternative_tool", "replan", "ask_user"
    alternative_tool: Optional[str] = None
    adjusted_parameters: Optional[Dict[str, Any]] = None
    message: str


class SelfCorrectionEngine:
    """Diagnoses execution failures and proposes automated corrective remedies."""

    @staticmethod
    def diagnose(error_str: str, tool_name: str, parameters: Dict[str, Any], retry_count: int, max_retries: int = 3) -> RecoveryPlan:
        err_lower = (error_str or "").lower()

        # Check maximum retry threshold
        if retry_count >= max_retries:
            return RecoveryPlan(
                cause=f"Exceeded maximum retry limit ({max_retries})",
                action="ask_user",
                message=f"KritiAI tried {retry_count} times but could not resolve: {error_str}. User intervention requested."
            )

        # 1. Shell / Command Error: Fallback between PowerShell and CMD
        if tool_name == "powershell" and ("is not recognized" in err_lower or "script execution" in err_lower):
            cmd = parameters.get("command", "")
            return RecoveryPlan(
                cause="PowerShell syntax or execution policy issue",
                action="alternative_tool",
                alternative_tool="cmd",
                adjusted_parameters={"command": cmd, "working_directory": parameters.get("working_directory")},
                message="Retrying command using Windows CMD shell."
            )

        # 2. File not found or path missing
        if "not found" in err_lower or "no such file" in err_lower:
            return RecoveryPlan(
                cause="Missing file or directory",
                action="retry",
                adjusted_parameters=parameters,
                message="Ensuring path structure and retrying operation."
            )

        # 3. Access Denied / Locked File
        if "access is denied" in err_lower or "permission denied" in err_lower:
            return RecoveryPlan(
                cause="File locked or permission boundary reached",
                action="ask_user",
                message=f"Access denied on target resource. Administrative elevation or approval needed: {error_str}"
            )

        # 4. General retry
        return RecoveryPlan(
            cause="Transient execution failure",
            action="retry",
            adjusted_parameters=parameters,
            message=f"Retrying action (attempt {retry_count + 1} of {max_retries})."
        )
