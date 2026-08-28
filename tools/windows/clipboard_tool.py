"""Windows Clipboard Tool for KritiAI."""
from typing import Any, Dict
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult


class ClipboardTool(BaseTool):
    """Safely inspect and write to the Windows clipboard."""
    name = "clipboard"
    description = "Read or write text to the Windows system clipboard."
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["read", "write"]},
            "text": {"type": "string", "description": "Text to write to clipboard", "optional": True}
        },
        "required": ["action"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "content": {"type": "string"},
            "length": {"type": "integer"}
        }
    }
    risk_level = RiskLevel.LOW
    required_permission = "allow_application_control"
    timeout_seconds = 10

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "read").lower()
        text = kwargs.get("text", "")

        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()

            if action == "read":
                try:
                    content = root.clipboard_get()
                except tk.TclError:
                    content = ""
                root.destroy()
                return ToolResult(
                    success=True,
                    data={"action": "read", "content": content, "length": len(content)},
                    verification={"verified": True, "reason": "Clipboard content retrieved."}
                )

            elif action == "write":
                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()
                root.destroy()
                return ToolResult(
                    success=True,
                    data={"action": "write", "length": len(text)},
                    verification={"verified": True, "reason": "Text placed on clipboard."}
                )

            root.destroy()
            return ToolResult(success=False, error=f"Unknown clipboard action '{action}'")

        except Exception as ex:
            return ToolResult(success=False, error=f"Clipboard error: {str(ex)}")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": execution_result.success, "reason": "Clipboard operation verified."}
