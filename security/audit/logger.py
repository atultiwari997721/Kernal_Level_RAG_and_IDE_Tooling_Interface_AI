"""Audit Logging for KritiAI Actions."""
from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from database.repository import Repository
from security.policies.models import PermissionDecision, RiskLevel

logger = logging.getLogger("kritiai.audit")


class AuditLogger:
    """Records every meaningful execution action into the persistent SQLite audit table."""

    def __init__(self, repo: Optional[Repository] = None):
        self.repo = repo or Repository()

    def log(
        self,
        tool: str,
        action: str,
        risk_level: RiskLevel,
        power_mode: str,
        decision: PermissionDecision,
        status: str,
        task_id: Optional[str] = None,
        agent: Optional[str] = None,
        details: Optional[Any] = None,
        verification_result: Optional[str] = None
    ) -> int:
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else None)
        log_id = self.repo.log_audit(
            tool=tool,
            action=action,
            risk_level=risk_level.value if isinstance(risk_level, RiskLevel) else str(risk_level),
            power_mode=power_mode,
            decision=decision.value if isinstance(decision, PermissionDecision) else str(decision),
            status=status,
            task_id=task_id,
            agent=agent,
            details=details_str,
            verification_result=verification_result
        )
        logger.info(
            f"[AUDIT] Task={task_id} Agent={agent} Tool={tool} Action={action} "
            f"Risk={risk_level} Mode={power_mode} Decision={decision} Status={status}"
        )
        return log_id

    def get_logs(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self.repo.get_audit_logs(task_id=task_id, limit=limit)
