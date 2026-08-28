"""Verification Engine for Validating Execution Outcomes."""
from typing import Any, Dict, Optional


class VerificationEngine:
    """Verifies whether an action had its intended real-world effect."""

    @staticmethod
    def verify_step(tool_output: Dict[str, Any], verification_condition: Optional[str] = None) -> Dict[str, Any]:
        """Examine tool execution results and verification payloads."""
        # If tool returned explicit verification
        if "verification" in tool_output and tool_output["verification"]:
            verif = tool_output["verification"]
            return {
                "verified": verif.get("verified", False),
                "reason": verif.get("reason", "Verification reported by tool.")
            }

        # Fallback to exit_code or success flag
        if tool_output.get("success") is True:
            return {"verified": True, "reason": "Operation completed without error."}
        else:
            return {
                "verified": False,
                "reason": tool_output.get("error") or "Operation failed execution."
            }
