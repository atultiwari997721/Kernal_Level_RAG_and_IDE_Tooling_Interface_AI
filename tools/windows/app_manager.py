"""Windows Application Manager Tool for KritiAI."""
import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
import psutil
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult

COMMON_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "edge": "msedge.exe",
    "chrome": "chrome.exe",
    "vscode": "code.cmd",
    "code": "code.cmd",
    "terminal": "wt.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe"
}


class ApplicationManagerTool(BaseTool):
    """Launch, inspect, and manage Windows desktop applications."""
    name = "app_manager"
    description = "Launch, close, or inspect desktop applications on Windows (e.g. VS Code, Notepad, Edge, Calculator)."
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["launch", "close", "list_known"]},
            "app_name": {"type": "string", "description": "Application name or executable (e.g., 'notepad', 'code', 'msedge')"},
            "arguments": {"type": "array", "items": {"type": "string"}, "optional": True}
        },
        "required": ["action"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "app": {"type": "string"},
            "pid": {"type": "integer"},
            "status": {"type": "string"},
            "verified": {"type": "boolean"}
        }
    }
    risk_level = RiskLevel.LOW
    required_permission = "allow_application_control"
    timeout_seconds = 30

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "launch").lower()
        app_name = kwargs.get("app_name", "").strip().lower()
        args = kwargs.get("arguments", [])

        if action == "close":
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW

        try:
            if action == "list_known":
                return ToolResult(
                    success=True,
                    data={"known_applications": list(COMMON_APPS.keys())}
                )

            elif action == "launch":
                exe_target = COMMON_APPS.get(app_name, app_name)
                # Locate executable
                resolved_exe = shutil.which(exe_target) or exe_target
                cmd_list = [resolved_exe] + args

                proc = subprocess.Popen(
                    cmd_list,
                    shell=True if exe_target.endswith(".cmd") or exe_target.endswith(".bat") else False,
                    creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0
                )
                time.sleep(0.5)

                verified = proc.poll() is None or psutil.pid_exists(proc.pid)
                verif = {
                    "verified": verified,
                    "reason": f"Application '{app_name}' launched with PID {proc.pid}" if verified else "Process exited immediately."
                }

                return ToolResult(
                    success=verified,
                    data={"app": app_name, "pid": proc.pid, "status": "running" if verified else "exited"},
                    verification=verif
                )

            elif action == "close":
                # Find by process name
                target_exe = COMMON_APPS.get(app_name, app_name)
                if not target_exe.endswith(".exe"):
                    target_exe += ".exe"
                closed_count = 0
                for p in psutil.process_iter(['name']):
                    try:
                        if p.info['name'] and p.info['name'].lower() == target_exe.lower():
                            p.terminate()
                            closed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                return ToolResult(
                    success=True,
                    data={"app": app_name, "closed_instances": closed_count},
                    verification={"verified": True, "reason": f"Closed {closed_count} instances of {app_name}."}
                )

            return ToolResult(success=False, error=f"Unknown app_manager action '{action}'")

        except Exception as ex:
            return ToolResult(success=False, error=f"App manager error: {str(ex)}")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": execution_result.success, "reason": "App action verified."}
