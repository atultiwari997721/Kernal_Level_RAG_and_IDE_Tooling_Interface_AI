"""Central Tool Registry with Policy Checking, Dry-Run, and Verification."""
import logging
import time
from typing import Any, Dict, List, Optional

from config.settings import AppConfig, get_config
from security.audit.logger import AuditLogger
from security.permissions.engine import PermissionEngine
from security.policies.models import PermissionDecision, RiskLevel
from security.sandbox.watchdog import get_emergency_stop_manager
from tools.base import BaseTool, ToolResult
from tools.filesystem.fs_tool import FilesystemTool
from tools.screenshot.screenshot_tool import ScreenshotTool
from tools.terminal.cmd_tool import CmdTool
from tools.terminal.powershell_tool import PowerShellTool
from tools.windows.app_manager import ApplicationManagerTool
from tools.windows.clipboard_tool import ClipboardTool
from tools.windows.process_manager import ProcessManagerTool
from tools.browser.browser_tool import BrowserTool
from tools.windows.system_info import SystemInfoTool
from tools.windows.ui_automation import UIAutomationTool

logger = logging.getLogger("kritiai.tools")


class ToolRegistry:
    """Manages all registered tools and executes them through deterministic security boundaries."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        permission_engine: Optional[PermissionEngine] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        self.config = config or get_config()
        self.permission_engine = permission_engine or PermissionEngine(self.config)
        self.audit_logger = audit_logger or AuditLogger()
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        defaults: List[BaseTool] = [
            FilesystemTool(),
            PowerShellTool(),
            CmdTool(),
            BrowserTool(),
            ProcessManagerTool(),
            ApplicationManagerTool(),
            SystemInfoTool(),
            ClipboardTool(),
            UIAutomationTool(),
            ScreenshotTool(),
        ]
        for t in defaults:
            self.register_tool(t)

    def register_tool(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._tools.values()]

    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        task_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Execute a tool with deterministic permission enforcement, dry-run support, and verification."""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not registered.",
                "decision": PermissionDecision.DENY.value,
                "verified": False
            }

        # Check Emergency Stop
        stop_mgr = get_emergency_stop_manager()
        if stop_mgr.is_stopped:
            return {
                "success": False,
                "error": "Emergency STOP is active. Execution denied.",
                "decision": PermissionDecision.DENY.value,
                "verified": False
            }

        action_name = parameters.get("operation") or parameters.get("action") or parameters.get("command") or tool_name
        target = parameters.get("path") or parameters.get("app_name") or parameters.get("command")

        # 1. Deterministic Policy Evaluation
        eval_result = self.permission_engine.evaluate(
            tool_name=tool_name,
            action=str(action_name),
            risk_level=tool.risk_level,
            target=str(target) if target else None,
            required_permission=tool.required_permission
        )

        if eval_result.decision == PermissionDecision.DENY:
            self.audit_logger.log(
                tool=tool_name,
                action=str(action_name),
                risk_level=tool.risk_level,
                power_mode=self.config.power_mode.value,
                decision=PermissionDecision.DENY,
                status="DENIED",
                task_id=task_id,
                agent=agent_name,
                details={"reason": eval_result.reason, "parameters": parameters}
            )
            return {
                "success": False,
                "error": f"Permission Denied: {eval_result.reason}",
                "decision": PermissionDecision.DENY.value,
                "verified": False
            }

        if eval_result.decision == PermissionDecision.ASK_USER:
            return {
                "success": False,
                "requires_approval": True,
                "prompt": eval_result.requires_approval_prompt or f"Allow {tool_name}:{action_name}?",
                "decision": PermissionDecision.ASK_USER.value,
                "tool_name": tool_name,
                "parameters": parameters,
                "verified": False
            }

        # 2. Dry-Run Mode
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "tool_name": tool_name,
                "parameters": parameters,
                "expected_risk": tool.risk_level.value,
                "decision": PermissionDecision.ALLOW.value,
                "message": f"[DRY RUN] Would execute {tool_name} with params: {parameters}"
            }

        # 3. Execution with Timeout and Observation
        start_t = time.time()
        try:
            params_with_task = dict(parameters)
            if task_id:
                params_with_task["task_id"] = task_id
            
            tool_result: ToolResult = tool.execute(**params_with_task)
            duration_ms = round((time.time() - start_t) * 1000, 2)

            status = "SUCCESS" if tool_result.success else "FAILED"
            verif_summary = tool_result.verification.get("reason") if tool_result.verification else None

            # 4. Audit Logging
            self.audit_logger.log(
                tool=tool_name,
                action=str(action_name),
                risk_level=tool.risk_level,
                power_mode=self.config.power_mode.value,
                decision=PermissionDecision.ALLOW,
                status=status,
                task_id=task_id,
                agent=agent_name,
                details=tool_result.data if tool_result.success else tool_result.error,
                verification_result=verif_summary
            )

            return {
                "success": tool_result.success,
                "data": tool_result.data,
                "error": tool_result.error,
                "verification": tool_result.verification,
                "verified": tool_result.verification.get("verified", False) if tool_result.verification else tool_result.success,
                "duration_ms": duration_ms,
                "decision": PermissionDecision.ALLOW.value
            }

        except Exception as ex:
            duration_ms = round((time.time() - start_t) * 1000, 2)
            self.audit_logger.log(
                tool=tool_name,
                action=str(action_name),
                risk_level=tool.risk_level,
                power_mode=self.config.power_mode.value,
                decision=PermissionDecision.ALLOW,
                status="ERROR",
                task_id=task_id,
                agent=agent_name,
                details=str(ex)
            )
            return {
                "success": False,
                "error": f"Tool execution crashed: {str(ex)}",
                "verified": False,
                "duration_ms": duration_ms,
                "decision": PermissionDecision.ALLOW.value
            }
