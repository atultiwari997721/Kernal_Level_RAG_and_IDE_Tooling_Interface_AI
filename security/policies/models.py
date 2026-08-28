"""Security Policy Definitions and Risk Classification."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class RiskLevel(str, Enum):
    """Action risk classification."""
    LOW = "low"            # Read file, inspect processes, search
    MEDIUM = "medium"      # Create folder/file, modify code, run safe dev command
    HIGH = "high"          # Delete files, run external network command, modify git remote
    CRITICAL = "critical"  # Irreversible system operations, format, delete root


class PermissionDecision(str, Enum):
    """Permission evaluation outcome."""
    ALLOW = "allow"
    DENY = "deny"
    ASK_USER = "ask_user"


class PolicyEvaluation(BaseModel):
    """Detailed evaluation result from the Permission Engine."""
    decision: PermissionDecision
    reason: str
    risk_level: RiskLevel
    tool_name: str
    action: str
    target: Optional[str] = None
    requires_approval_prompt: Optional[str] = None
