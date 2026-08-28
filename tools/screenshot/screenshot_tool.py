"""Windows Screen Capture Tool for KritiAI."""
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
from config.settings import get_config
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult


class ScreenshotTool(BaseTool):
    """Captures screenshots on Windows for visual inspection and UI verification."""
    name = "screenshot"
    description = "Capture full screen or specific bounding region on Windows and save locally."
    input_schema = {
        "type": "object",
        "properties": {
            "region": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Optional bounding box [x, y, width, height]",
                "optional": True
            },
            "filename": {"type": "string", "description": "Optional custom filename", "optional": True}
        }
    }
    output_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "width": {"type": "integer"},
            "height": {"type": "integer"},
            "format": {"type": "string"}
        }
    }
    risk_level = RiskLevel.LOW
    required_permission = "allow_application_control"
    timeout_seconds = 15

    def execute(self, **kwargs: Any) -> ToolResult:
        region = kwargs.get("region")
        custom_name = kwargs.get("filename")
        config = get_config()
        shots_dir = config.data_dir / "screenshots"
        shots_dir.mkdir(parents=True, exist_ok=True)

        filename = custom_name or f"screenshot_{int(time.time() * 1000)}.png"
        if not filename.endswith(".png"):
            filename += ".png"
        output_path = shots_dir / filename

        try:
            import pyautogui
            if region and len(region) == 4:
                shot = pyautogui.screenshot(region=tuple(region))
            else:
                shot = pyautogui.screenshot()
            
            shot.save(str(output_path))
            
            verified = output_path.is_file() and output_path.stat().st_size > 0
            data = {
                "file_path": str(output_path),
                "width": shot.width,
                "height": shot.height,
                "format": "PNG",
                "size_bytes": output_path.stat().st_size
            }

            return ToolResult(
                success=verified,
                data=data,
                verification={"verified": verified, "reason": f"Screenshot saved to {output_path}"}
            )

        except ImportError:
            return ToolResult(success=False, error="pyautogui required for screenshot capture.")
        except Exception as ex:
            return ToolResult(success=False, error=f"Screenshot error: {str(ex)}")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": execution_result.success, "reason": "Screenshot verified."}
