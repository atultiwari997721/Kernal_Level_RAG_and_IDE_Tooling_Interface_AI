"""Goal Understanding Engine for KritiAI."""
import os
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel
from security.policies.models import RiskLevel


class GoalIntent(BaseModel):
    """Structured understanding of the user's objective."""
    raw_goal: str
    intent_type: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = {}
    estimated_risk: RiskLevel = RiskLevel.MEDIUM
    requires_terminal: bool = False
    working_directory: str = ""


class GoalEngine:
    """Parses natural language objectives into structured execution intents."""

    def __init__(self, default_workdir: Optional[str] = None):
        self.default_workdir = default_workdir or os.getcwd()

    def understand_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> GoalIntent:
        g_clean = goal.strip()
        g_lower = g_clean.lower()
        workdir = (context or {}).get("working_directory") or self.default_workdir

        # 1. Folder Creation: "Create a folder called Test", "mkdir MyFolder"
        folder_match = re.search(
            r"(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)(?:\s+(?:called|named))?\s+([^\s\.\,\;]+)",
            g_clean,
            re.IGNORECASE
        )
        if folder_match:
            folder_name = folder_match.group(1).strip("\"'")
            target_path = os.path.join(workdir, folder_name)
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="create_folder",
                target=target_path,
                parameters={"path": target_path},
                estimated_risk=RiskLevel.MEDIUM,
                working_directory=workdir
            )

        # 2. File Creation: "Create a file called script.py with content print('hello')"
        file_match = re.search(
            r"(?:create|make|write)\s+(?:a\s+)?file(?:\s+(?:called|named))?\s+([^\s\,]+)",
            g_clean,
            re.IGNORECASE
        )
        if file_match:
            file_name = file_match.group(1).strip("\"'")
            target_path = os.path.join(workdir, file_name)
            content_match = re.search(r"(?:with\s+content|containing)\s+[\"']?(.*?)[\"']?$", g_clean, re.IGNORECASE)
            content = content_match.group(1) if content_match else ""
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="create_file",
                target=target_path,
                parameters={"path": target_path, "content": content},
                estimated_risk=RiskLevel.MEDIUM,
                working_directory=workdir
            )

        # 3. Application Launch: "Open VS Code", "Launch Notepad"
        app_match = re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_-]+)", g_lower)
        if app_match and any(app in g_lower for app in ["notepad", "calc", "calculator", "edge", "chrome", "code", "vscode", "terminal"]):
            app_name = app_match.group(1)
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="launch_app",
                target=app_name,
                parameters={"app_name": app_name},
                estimated_risk=RiskLevel.LOW,
                working_directory=workdir
            )

        # 4. Hardware / Telemetry: "System info", "Check hardware"
        if "hardware" in g_lower or "system info" in g_lower or "telemetry" in g_lower:
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="system_info",
                target="system",
                parameters={"detailed": True},
                estimated_risk=RiskLevel.LOW,
                working_directory=workdir
            )

        # 5. Terminal / Dev execution: "run pip install ...", "run git status", "npm test"
        if any(w in g_lower for w in ["pip ", "npm ", "git ", "python ", "pytest", "run "]):
            cmd = g_clean.replace("run ", "").strip()
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="terminal_command",
                target=cmd,
                parameters={"command": cmd, "working_directory": workdir},
                estimated_risk=RiskLevel.MEDIUM,
                requires_terminal=True,
                working_directory=workdir
            )

        # 6. General Goal fallback
        return GoalIntent(
            raw_goal=g_clean,
            intent_type="general_goal",
            target=g_clean,
            parameters={"goal": g_clean},
            estimated_risk=RiskLevel.MEDIUM,
            working_directory=workdir
        )
