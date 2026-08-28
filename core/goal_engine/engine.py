"""Goal Understanding Engine for KritiAI with Media and Location-Aware App Scaffolding."""
import os
import re
from pathlib import Path
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

    def _resolve_target_path(self, raw_path: str, default_name: str, workdir: str) -> str:
        r"""Resolve any Windows path: absolute (K:\...), Desktop, relative, or current."""
        clean = raw_path.strip().strip("\"'")
        clean_lower = clean.lower()

        # Handle 'desktop'
        if "desktop" in clean_lower:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            subfolder = clean_lower.replace("on desktop", "").replace("in desktop", "").replace("desktop", "").strip(" /\\")
            return os.path.join(desktop_dir, subfolder or default_name)

        # Handle 'downloads' or 'documents'
        if "downloads" in clean_lower:
            return os.path.join(os.path.expanduser("~"), "Downloads", default_name)
        if "documents" in clean_lower:
            return os.path.join(os.path.expanduser("~"), "Documents", default_name)

        # Check if it has a Windows drive letter e.g. K:\... or C:\...
        if re.match(r"^[A-Za-z]:[\\/]", clean):
            return os.path.normpath(clean)

        # Check if user specified a path like "K:\Projects\calc" inside text
        drive_match = re.search(r"([A-Za-z]:[\\/][^\s\"']+)", clean)
        if drive_match:
            return os.path.normpath(drive_match.group(1))

        # Relative to working directory
        return os.path.normpath(os.path.join(workdir, clean or default_name))

    def understand_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> GoalIntent:
        g_clean = goal.strip()
        g_lower = g_clean.lower()
        workdir = (context or {}).get("working_directory") or self.default_workdir

        # 1. Media / YouTube Playback Intent: "Play Sita Ram song", "Open YouTube and play Sita Ram"
        if any(g_lower.startswith(prefix) for prefix in ["play ", "open youtube", "listen to "]) or "play " in g_lower:
            query = g_clean
            # Clean up query
            for phrase in ["open youtube and play", "open youtube and search", "open youtube to play", "play on youtube", "play song", "play video", "play"]:
                if phrase in query.lower():
                    # Case-insensitive replacement of command trigger
                    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                    query = pattern.sub("", query).strip()
            # Remove trailing 'song' or 'on youtube'
            query = re.sub(r"\s+on\s+youtube$", "", query, flags=re.IGNORECASE).strip()
            query = query.strip("\"' ")
            if not query:
                query = "Sita Ram song"

            return GoalIntent(
                raw_goal=g_clean,
                intent_type="play_youtube",
                target=query,
                parameters={"query": query, "operation": "play_youtube"},
                estimated_risk=RiskLevel.LOW,
                working_directory=workdir
            )

        # 2. Specific Location Calculator App Intent: "Create calculator on K:\Test\Calc", "Make a calculator app on Desktop"
        calc_match = re.search(
            r"(?:create|make|build|scaffold)\s+(?:a\s+)?(?:working\s+|functional\s+)?calculator(?:\s+app|\s+project)?(?:\s+(?:on|in|at)\s+(.+))?",
            g_clean,
            re.IGNORECASE
        )
        if calc_match or "calculator" in g_lower and any(w in g_lower for w in ["create", "make", "build", "scaffold"]):
            raw_loc = calc_match.group(1) if (calc_match and calc_match.group(1)) else ""
            if not raw_loc:
                # Look for drive or directory pattern
                drive_find = re.search(r"(?:in|at|on|to)\s+([A-Za-z]:[\\/][^\s\"']+)", g_clean)
                if drive_find:
                    raw_loc = drive_find.group(1)

            target_path = self._resolve_target_path(raw_loc, "Calculator", workdir)
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="create_calculator",
                target=target_path,
                parameters={"path": target_path, "app_type": "calculator"},
                estimated_risk=RiskLevel.MEDIUM,
                working_directory=target_path
            )

        # 3. Web Navigation / Search: "Open google", "Search for best LLMs"
        if g_lower.startswith("search ") or "search web for" in g_lower:
            search_query = re.sub(r"^(?:search\s+for|search\s+the\s+web\s+for|search\s+web\s+for|search)\s+", "", g_clean, flags=re.IGNORECASE).strip()
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="search_web",
                target=search_query,
                parameters={"query": search_query, "engine": "google"},
                estimated_risk=RiskLevel.LOW,
                working_directory=workdir
            )

        # 4. Folder Creation: "Create a folder called Test", "mkdir MyFolder"
        folder_match = re.search(
            r"(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)(?:\s+(?:called|named))?\s+([^\s\.\,\;]+)",
            g_clean,
            re.IGNORECASE
        )
        if folder_match:
            folder_name = folder_match.group(1).strip("\"'")
            target_path = self._resolve_target_path(folder_name, folder_name, workdir)
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="create_folder",
                target=target_path,
                parameters={"path": target_path},
                estimated_risk=RiskLevel.MEDIUM,
                working_directory=workdir
            )

        # 5. File Creation: "Create a file called script.py with content print('hello')"
        file_match = re.search(
            r"(?:create|make|write)\s+(?:a\s+)?file(?:\s+(?:called|named))?\s+([^\s\,]+)",
            g_clean,
            re.IGNORECASE
        )
        if file_match:
            file_name = file_match.group(1).strip("\"'")
            target_path = self._resolve_target_path(file_name, file_name, workdir)
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

        # 6. Application Launch: "Open VS Code", "Launch Notepad", "Open calc"
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

        # 7. Hardware / Telemetry: "System info", "Check hardware"
        if "hardware" in g_lower or "system info" in g_lower or "telemetry" in g_lower:
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="system_info",
                target="system",
                parameters={"detailed": True},
                estimated_risk=RiskLevel.LOW,
                working_directory=workdir
            )

        # 8. Terminal / Dev execution: "run pip install ...", "run git status", "npm test"
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

        # 9. General Goal fallback
        return GoalIntent(
            raw_goal=g_clean,
            intent_type="general_goal",
            target=g_clean,
            parameters={"goal": g_clean},
            estimated_risk=RiskLevel.MEDIUM,
            working_directory=workdir
        )
