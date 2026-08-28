"""Windows UI Automation, Keyboard, and Mouse Tool for KritiAI."""
import time
from typing import Any, Dict, List, Optional
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult


class UIAutomationTool(BaseTool):
    """Interacts with the Windows UI via keyboard and mouse events."""
    name = "ui_automation"
    description = "Perform controlled mouse clicks, keyboard typing, and hotkeys on Windows."
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["click", "double_click", "type_text", "hotkey", "scroll", "move_to"]},
            "x": {"type": "integer", "description": "X screen coordinate", "optional": True},
            "y": {"type": "integer", "description": "Y screen coordinate", "optional": True},
            "text": {"type": "string", "description": "Text to type", "optional": True},
            "keys": {"type": "array", "items": {"type": "string"}, "description": "Keys for hotkey combo (e.g. ['ctrl', 'c'])", "optional": True},
            "clicks": {"type": "integer", "description": "Scroll amount", "optional": True},
        },
        "required": ["action"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "executed": {"type": "boolean"},
            "details": {"type": "object"}
        }
    }
    risk_level = RiskLevel.MEDIUM
    required_permission = "allow_keyboard_mouse"
    timeout_seconds = 15

    def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "").lower()
        x = kwargs.get("x")
        y = kwargs.get("y")
        text = kwargs.get("text", "")
        keys = kwargs.get("keys", [])
        clicks = kwargs.get("clicks", 0)

        try:
            import pyautogui
            pyautogui.FAILSAFE = True

            if action == "click":
                if x is not None and y is not None:
                    pyautogui.click(x=x, y=y)
                else:
                    pyautogui.click()
                details = {"clicked_at": (x, y)}

            elif action == "double_click":
                if x is not None and y is not None:
                    pyautogui.doubleClick(x=x, y=y)
                else:
                    pyautogui.doubleClick()
                details = {"double_clicked_at": (x, y)}

            elif action == "type_text":
                pyautogui.write(text, interval=0.02)
                details = {"typed_length": len(text)}

            elif action == "hotkey":
                if not keys:
                    return ToolResult(success=False, error="No keys provided for hotkey action.")
                pyautogui.hotkey(*keys)
                details = {"hotkey": "+".join(keys)}

            elif action == "scroll":
                pyautogui.scroll(clicks)
                details = {"scroll_amount": clicks}

            elif action == "move_to":
                if x is None or y is None:
                    return ToolResult(success=False, error="Coordinates x and y required for move_to.")
                pyautogui.moveTo(x, y, duration=0.2)
                details = {"moved_to": (x, y)}

            else:
                return ToolResult(success=False, error=f"Unknown UI automation action: {action}")

            return ToolResult(
                success=True,
                data={"action": action, "executed": True, "details": details},
                verification={"verified": True, "reason": f"Action {action} performed successfully."}
            )

        except ImportError:
            return ToolResult(success=False, error="pyautogui module not available for UI automation.")
        except Exception as ex:
            return ToolResult(success=False, error=f"UI automation error: {str(ex)}")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": execution_result.success, "reason": "UI action completed."}
