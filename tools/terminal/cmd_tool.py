"""Windows CMD Tool for KritiAI Execution."""
from typing import Any, Dict, Optional
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult
from tools.terminal.runner import CommandRunner
from tools.terminal.safety import CommandSafetyClassifier


class CmdTool(BaseTool):
    """Executes commands in Windows CMD."""
    name = "cmd"
    description = "Execute commands in the standard Windows Command Prompt (cmd.exe)."
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command line to execute in cmd.exe"},
            "working_directory": {"type": "string", "description": "Working directory for execution"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
        },
        "required": ["command"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "exit_code": {"type": "integer"},
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "duration": {"type": "number"},
            "timed_out": {"type": "boolean"},
            "status": {"type": "string"},
        }
    }
    risk_level = RiskLevel.MEDIUM
    required_permission = "allow_terminal"
    timeout_seconds = 60

    def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs.get("command", "")
        working_dir = kwargs.get("working_directory")
        timeout = kwargs.get("timeout", self.timeout_seconds)
        task_id = kwargs.get("task_id")

        risk, _ = CommandSafetyClassifier.classify(command)
        self.risk_level = risk

        result = CommandRunner.execute(
            command=command,
            shell="cmd",
            working_directory=working_dir,
            timeout=timeout,
            task_id=task_id
        )

        success = result["status"] == "SUCCESS" and result["exit_code"] == 0
        error = result["stderr"] if not success else None

        verification = self.verify(
            ToolResult(success=success, data=result, error=error),
            expected_output=kwargs.get("expected_output")
        )

        return ToolResult(
            success=success,
            data=result,
            error=error,
            verification=verification,
            duration_ms=result.get("duration", 0) * 1000
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        expected = kwargs.get("expected_output")
        data = execution_result.data or {}
        stdout = data.get("stdout", "")
        exit_code = data.get("exit_code", -1)

        verified = (exit_code == 0)
        reason = f"CMD command finished with exit code {exit_code}"

        if expected and verified:
            if expected.lower() in stdout.lower():
                reason += f" and stdout contained '{expected}'"
            else:
                verified = False
                reason += f" but stdout lacked '{expected}'"

        return {
            "verified": verified,
            "exit_code": exit_code,
            "reason": reason
        }
