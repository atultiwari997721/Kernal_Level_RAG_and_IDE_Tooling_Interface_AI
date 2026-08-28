"""Windows Process Management Tool for KritiAI."""
from typing import Any, Dict, List, Optional
import psutil
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult


class ProcessManagerTool(BaseTool):
    """Inspect and manage running Windows processes."""
    name = "process_manager"
    description = "List, inspect, and terminate running processes on Windows."
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list", "inspect", "terminate", "find_by_name"]},
            "pid": {"type": "integer", "description": "Process ID for inspect or terminate", "optional": True},
            "process_name": {"type": "string", "description": "Process name pattern to find", "optional": True},
            "limit": {"type": "integer", "description": "Maximum processes to return (default 50)", "optional": True}
        },
        "required": ["action"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "processes": {"type": "array"},
            "count": {"type": "integer"},
            "status": {"type": "string"}
        }
    }
    risk_level = RiskLevel.LOW
    required_permission = "allow_application_control"
    timeout_seconds = 20

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "list").lower()
        pid = kwargs.get("pid")
        name_filter = kwargs.get("process_name", "").lower()
        limit = kwargs.get("limit", 50)

        if action == "terminate":
            self.risk_level = RiskLevel.HIGH
        else:
            self.risk_level = RiskLevel.LOW

        try:
            if action == "list":
                procs = []
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
                    try:
                        info = p.info
                        mem = round(info['memory_info'].rss / (1024 * 1024), 2) if info.get('memory_info') else 0
                        procs.append({
                            "pid": info['pid'],
                            "name": info['name'],
                            "cpu_percent": info.get('cpu_percent', 0),
                            "memory_mb": mem,
                            "status": info.get('status', 'running')
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    if len(procs) >= limit:
                        break
                return ToolResult(success=True, data={"processes": procs, "count": len(procs)})

            elif action == "find_by_name":
                matches = []
                for p in psutil.process_iter(['pid', 'name', 'status']):
                    try:
                        p_name = p.info['name'].lower()
                        if name_filter in p_name:
                            matches.append({"pid": p.info['pid'], "name": p.info['name'], "status": p.info['status']})
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return ToolResult(success=True, data={"matches": matches, "count": len(matches)})

            elif action == "inspect":
                if not pid or not psutil.pid_exists(pid):
                    return ToolResult(success=False, error=f"Process PID {pid} does not exist.")
                p = psutil.Process(pid)
                mem = round(p.memory_info().rss / (1024 * 1024), 2)
                data = {
                    "pid": p.pid,
                    "name": p.name(),
                    "exe": p.exe() if hasattr(p, 'exe') else None,
                    "cpu_percent": p.cpu_percent(interval=0.1),
                    "memory_mb": mem,
                    "status": p.status(),
                    "num_threads": p.num_threads()
                }
                return ToolResult(success=True, data=data)

            elif action == "terminate":
                if not pid or not psutil.pid_exists(pid):
                    return ToolResult(success=False, error=f"Process PID {pid} not found.")
                p = psutil.Process(pid)
                p.terminate()
                p.wait(timeout=3)
                verified = not psutil.pid_exists(pid)
                return ToolResult(
                    success=verified,
                    data={"terminated_pid": pid, "status": "terminated"},
                    verification={"verified": verified, "reason": "Process is no longer in process table."}
                )

            return ToolResult(success=False, error=f"Unknown action '{action}'")

        except Exception as ex:
            return ToolResult(success=False, error=f"Process manager error: {str(ex)}")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": execution_result.success, "reason": "Process operation confirmed"}
