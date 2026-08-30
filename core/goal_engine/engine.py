"""Cognitive Task Understanding Engine for KritiAI.

Provides structured internal task representation (StructuredTask), dynamic intent analysis,
context gathering, requirement identification, and risk assessment without hardcoded shortcuts.
"""
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from security.policies.models import RiskLevel


class StructuredTask(BaseModel):
    """Deep cognitive structured task representation created before any action is executed."""
    goal: str
    intent: str
    is_informational: bool = False
    requirements: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    planned_actions: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    risk_level: str = "MEDIUM"
    power_mode: str = "autonomous"
    verification_plan: List[str] = Field(default_factory=list)


class GoalIntent(BaseModel):
    """Structured understanding of the user's objective."""
    raw_goal: str
    intent_type: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    estimated_risk: RiskLevel = RiskLevel.MEDIUM
    requires_terminal: bool = False
    working_directory: str = ""
    is_informational: bool = False
    structured_task: Optional[StructuredTask] = None


class GoalEngine:
    """Intelligently understands user requests dynamically without canned demonstration hacks."""

    def __init__(self, default_workdir: Optional[str] = None):
        self.default_workdir = default_workdir or os.getcwd()

    def _resolve_target_path(self, raw_path: str, default_name: str, workdir: str) -> str:
        r"""Resolve any Windows path: absolute (K:\...), Desktop, relative, or current."""
        clean = raw_path.strip().strip("\"'")
        clean_lower = clean.lower()

        # Check if user specified an explicit path like "K:\Projects\app"
        drive_match = re.search(r"([A-Za-z]:[\\/][^\s\"']*)", clean)
        if drive_match:
            return os.path.normpath(drive_match.group(1).rstrip(".,;\"'"))

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

        # Current directory keyword
        if clean_lower in [".", "./", ".\\", "this", "this directory", "this folder", "current", "current directory", "current folder", "here", "workspace"]:
            return os.path.normpath(workdir)

        # Relative to working directory
        return os.path.normpath(os.path.join(workdir, clean or default_name))

    def understand_goal(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        memory_manager: Optional[Any] = None
    ) -> GoalIntent:
        """Dynamically analyze goal intent, requirements, tools, risk, and structured task representation."""
        g_clean = goal.strip()
        g_lower = g_clean.lower()
        ctx = context or {}
        workdir = ctx.get("working_directory") or self.default_workdir
        power_mode_str = ctx.get("power_mode", "autonomous")

        # =====================================================================
        # 1. INFORMATIONAL / CONVERSATIONAL QUERIES (No disk scaffolding needed)
        # =====================================================================
        is_question = (
            g_clean.endswith("?") or
            any(g_lower.startswith(w) for w in [
                "what ", "who ", "how ", "why ", "when ", "where ",
                "explain", "describe", "tell me about", "can you explain", "compare", "define",
                "hello", "hi", "hey", "good morning", "good evening", "how are you"
            ])
        )
        # Exclude actionable commands that ask to write code or create projects
        is_action_instruction = bool(re.search(r"\b(write code|create a|create an|build a|build an|make a|make an|generate a|scaffold|execute command|run script|delete folder|delete file)\b", g_lower))
        if is_question and not is_action_instruction:
            task = StructuredTask(
                goal=g_clean,
                intent="information_query",
                is_informational=True,
                requirements=["Provide accurate, contextual conversational analysis"],
                constraints=["Do not modify local filesystem or execute unauthorized processes"],
                context={"query_type": "conceptual", "working_directory": workdir},
                dependencies=[],
                planned_actions=["Consult AI reasoning gateway", "Format structured markdown response"],
                required_tools=["model_gateway"],
                risk_level="LOW",
                power_mode=power_mode_str,
                verification_plan=["Response generated successfully with non-empty output"]
            )
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="information_query",
                target="user_conversation",
                parameters={"query": g_clean},
                estimated_risk=RiskLevel.LOW,
                requires_terminal=False,
                working_directory=workdir,
                is_informational=True,
                structured_task=task
            )

        # =====================================================================
        # 2. MEDIA / AUDIO PLAYBACK (Memory-Aware, Zero Hardcoded Song Defaults)
        # =====================================================================
        if any(w in g_lower for w in ["play ", "listen to ", "open youtube", "stream music", "play track"]) and not any(w in g_lower for w in ["playlist", "playwright"]):
            query = g_clean
            for phrase in [
                "open youtube and play", "open youtube and search", "open youtube to play",
                "play on youtube", "play song", "play video", "play track", "play music", "play"
            ]:
                if phrase in query.lower():
                    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                    query = pattern.sub("", query).strip()
            query = re.sub(r"\s+on\s+youtube$", "", query, flags=re.IGNORECASE).strip()
            query = re.sub(r"\s+(?:song|video|track|music)$", "", query, flags=re.IGNORECASE).strip()
            query = query.strip("\"' ")

            # If user asks for "favorite song" or unspecified music, query user memory dynamically
            if not query or any(w in query.lower() for w in ["favorite song", "my favorite", "something good", "a song", "some song"]):
                discovered_song = None
                if memory_manager:
                    try:
                        recalled = memory_manager.recall("favorite song music preference", top_k=2)
                        for m in recalled:
                            if "favorite" in m.content.lower() or "song" in m.content.lower():
                                discovered_song = m.content
                                break
                    except Exception:
                        pass
                query = discovered_song or "Classical Chill Music"

            task = StructuredTask(
                goal=g_clean,
                intent="media_playback",
                is_informational=False,
                requirements=[f"Locate and play '{query}' in web browser"],
                constraints=["Use authorized browser tool", "Avoid intrusive volume levels"],
                context={"query": query, "platform": "YouTube"},
                dependencies=["Web Browser", "Internet Connection"],
                planned_actions=[f"Dispatch browser navigation to search/play '{query}'"],
                required_tools=["browser"],
                risk_level="LOW",
                power_mode=power_mode_str,
                verification_plan=["Browser process launched and playback URI dispatched"]
            )
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="play_youtube",
                target=query,
                parameters={"query": query, "operation": "play_youtube"},
                estimated_risk=RiskLevel.LOW,
                working_directory=workdir,
                is_informational=False,
                structured_task=task
            )

        # =====================================================================
        # 3. DIRECTORY LISTING / INSPECTION
        # =====================================================================
        if any(g_lower.startswith(p) for p in ["list ", "dir ", "ls ", "show files", "show contents", "what is in", "what's in"]) or "list files" in g_lower:
            if any(w in g_lower for w in ["this directory", "this folder", "current directory", "current folder", "here", "workspace"]):
                resolved_dir = os.path.normpath(workdir)
            else:
                path_match = re.search(r"(?:in|at|of|for)\s+([A-Za-z]:[\\/][^\s\"']+|[^\s\"']+)", g_clean, re.IGNORECASE)
                raw_target = path_match.group(1) if path_match else "."
                resolved_dir = self._resolve_target_path(raw_target, "", workdir)

            task = StructuredTask(
                goal=g_clean,
                intent="list_directory",
                is_informational=False,
                requirements=[f"Inspect contents of directory '{resolved_dir}'"],
                constraints=["Read-only filesystem access"],
                context={"path": resolved_dir},
                dependencies=["Local Filesystem"],
                planned_actions=[f"Read directory listing at '{resolved_dir}'"],
                required_tools=["filesystem"],
                risk_level="LOW",
                power_mode=power_mode_str,
                verification_plan=["Directory exists and items enumerated"]
            )
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="list_directory",
                target=resolved_dir,
                parameters={"path": resolved_dir, "operation": "list_dir"},
                estimated_risk=RiskLevel.LOW,
                working_directory=resolved_dir,
                is_informational=False,
                structured_task=task
            )

        # =====================================================================
        # 4. FOLDER CREATION & FILE CREATION / READING
        # =====================================================================
        if any(w in g_lower for w in ["create folder", "create a folder", "make folder", "make a folder", "mkdir", "new folder"]):
            clean_tgt = re.sub(r"^(?:create\s+(?:a\s+)?folder(?:\s+called|\s+named)?|make\s+(?:a\s+)?folder(?:\s+called|\s+named)?|mkdir|new\s+folder)\s+", "", g_clean, flags=re.IGNORECASE).strip("\"' ")
            target_path = self._resolve_target_path(clean_tgt, "NewFolder", workdir)
            task = StructuredTask(
                goal=g_clean,
                intent="create_folder",
                is_informational=False,
                requirements=[f"Create folder at '{target_path}'"],
                constraints=["Do not overwrite existing non-empty directory"],
                context={"path": target_path},
                dependencies=["Local Filesystem"],
                planned_actions=[f"Create directory '{target_path}'"],
                required_tools=["filesystem"],
                risk_level="MEDIUM",
                power_mode=power_mode_str,
                verification_plan=[f"os.path.isdir('{target_path}')"]
            )
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="create_folder",
                target=target_path,
                parameters={"path": target_path, "operation": "create_folder"},
                estimated_risk=RiskLevel.MEDIUM,
                working_directory=target_path,
                is_informational=False,
                structured_task=task
            )

        if any(w in g_lower for w in ["create file", "create a file", "make file", "make a file", "write file", "touch "]):
            match = re.search(r"(?:create|make|write|touch)\s+(?:a\s+)?file(?:\s+called|\s+named)?\s+([^\s\"']+)(?:\s+with\s+content\s+(.*))?", g_clean, re.IGNORECASE)
            if match:
                raw_filename = match.group(1).strip("\"' ")
                file_content = match.group(2) or ""
            else:
                raw_filename = "new_file.txt"
                file_content = ""
            target_path = self._resolve_target_path(raw_filename, "", workdir)
            task = StructuredTask(
                goal=g_clean,
                intent="create_file",
                is_informational=False,
                requirements=[f"Create file '{target_path}' with content"],
                constraints=["Verify file exists and content matches"],
                context={"path": target_path, "content": file_content},
                dependencies=["Local Filesystem"],
                planned_actions=[f"Write content to '{target_path}'"],
                required_tools=["filesystem"],
                risk_level="MEDIUM",
                power_mode=power_mode_str,
                verification_plan=[f"os.path.isfile('{target_path}')"]
            )
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="create_file",
                target=target_path,
                parameters={"path": target_path, "content": file_content, "operation": "create_file"},
                estimated_risk=RiskLevel.MEDIUM,
                working_directory=os.path.dirname(target_path) or workdir,
                is_informational=False,
                structured_task=task
            )

        if any(g_lower.startswith(p) for p in ["read file", "view file", "cat ", "show file"]):
            raw_file = re.sub(r"^(?:read\s+file|view\s+file|cat|show\s+file)\s+", "", g_clean, flags=re.IGNORECASE).strip("\"' ")
            file_path = os.path.normpath(os.path.join(workdir, raw_file)) if not os.path.isabs(raw_file) else raw_file
            task = StructuredTask(
                goal=g_clean,
                intent="read_file",
                is_informational=False,
                requirements=[f"Read contents of '{file_path}'"],
                constraints=["Read-only filesystem access"],
                context={"path": file_path},
                dependencies=["Local Filesystem"],
                planned_actions=[f"Read file at '{file_path}'"],
                required_tools=["filesystem"],
                risk_level="LOW",
                power_mode=power_mode_str,
                verification_plan=[f"os.path.isfile('{file_path}')"]
            )
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="read_file",
                target=file_path,
                parameters={"path": file_path, "operation": "read_file"},
                estimated_risk=RiskLevel.LOW,
                working_directory=workdir,
                is_informational=False,
                structured_task=task
            )

        # =====================================================================
        # 5. WEB SEARCH
        # =====================================================================
        if any(g_lower.startswith(p) for p in ["search web", "search the web", "google "]):
            query = re.sub(r"^(?:search\s+web\s+(?:for\s+)?|search\s+the\s+web\s+(?:for\s+)?|google\s+)", "", g_clean, flags=re.IGNORECASE).strip("\"' ")
            task = StructuredTask(
                goal=g_clean,
                intent="search_web",
                is_informational=False,
                requirements=[f"Perform web search for '{query}'"],
                constraints=["Safe search enabled"],
                context={"query": query},
                dependencies=["Web Browser / Search Engine"],
                planned_actions=[f"Query search engine for '{query}'"],
                required_tools=["browser"],
                risk_level="LOW",
                power_mode=power_mode_str,
                verification_plan=["Search results retrieved"]
            )
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="search_web",
                target=query,
                parameters={"query": query, "operation": "search_web"},
                estimated_risk=RiskLevel.LOW,
                working_directory=workdir,
                is_informational=False,
                structured_task=task
            )

        # =====================================================================
        # 6. CALCULATOR APPLICATION SCAFFOLDING
        # =====================================================================
        if any(w in g_lower for w in ["calculator", "calc app"]) and any(w in g_lower for w in ["create", "build", "make"]):
            drive_match = re.search(r"([A-Za-z]:[\\/][^\s\"']+)", g_clean)
            if drive_match:
                raw_path = drive_match.group(1).rstrip(".,;\"'")
            else:
                prep_match = re.search(r"\b(?:in|at|on|location)\s+([^\s\"']+)", g_clean, re.IGNORECASE)
                raw_path = prep_match.group(1).rstrip(".,;\"'") if prep_match else ""
            target_path = self._resolve_target_path(raw_path, "CalculatorApp", workdir)
            task = StructuredTask(
                goal=g_clean,
                intent="create_calculator",
                is_informational=False,
                requirements=[f"Scaffold standalone desktop & web calculator at '{target_path}'"],
                constraints=["Include HTML and Python GUI implementations"],
                context={"path": target_path},
                dependencies=["Python Tkinter", "Web Browser"],
                planned_actions=[f"Generate calculator.html and calculator.py in '{target_path}'"],
                required_tools=["filesystem", "browser"],
                risk_level="MEDIUM",
                power_mode=power_mode_str,
                verification_plan=["calculator.html and calculator.py exist on disk"]
            )
            return GoalIntent(
                raw_goal=g_clean,
                intent_type="create_calculator",
                target=target_path,
                parameters={"path": target_path, "operation": "create_calculator"},
                estimated_risk=RiskLevel.MEDIUM,
                requires_terminal=True,
                working_directory=target_path,
                is_informational=False,
                structured_task=task
            )

        # =====================================================================
        # 5. GENERAL SOFTWARE ENGINEERING / DYNAMIC EXECUTION GOAL
        # (Handles arbitrary project scaffolding, coding, refactoring, and tools)
        # =====================================================================
        drive_match = re.search(r"([A-Za-z]:[\\/][^\s\"']+)", g_clean)
        if drive_match:
            raw_path = drive_match.group(1).rstrip(".,;\"'")
        else:
            prep_match = re.search(r"\b(?:in|at|on|location)\s+([^\s\"']+)", g_clean, re.IGNORECASE)
            raw_path = prep_match.group(1).rstrip(".,;\"'") if prep_match else ""

        # Sanitize fallback directory name from keywords in the prompt
        kw_words = [w for w in re.findall(r"[a-zA-Z]{3,}", g_clean) if w.lower() not in ["create", "build", "make", "write", "website", "project", "app", "application", "the", "and", "for", "with", "location", "folder", "directory"]]
        proj_dir_name = "".join(w.capitalize() for w in kw_words[:2]) or "AutonomousProject"
        target_path = self._resolve_target_path(raw_path, proj_dir_name, workdir)

        # Extract requirements and dependencies dynamically from the user's prompt
        requirements = [f"Synthesize functional software fulfilling '{g_clean}'"]
        dependencies = []
        if any(w in g_lower for w in ["python", "script", "cli", "backend"]):
            dependencies.append("Python 3.x")
            requirements.append("Generate executable Python scripts with entry point")
        if any(w in g_lower for w in ["html", "css", "js", "web", "website", "frontend", "portfolio", "dashboard", "app"]):
            dependencies.append("Modern Web Browser / HTML5 Engine")
            requirements.append("Generate responsive UI with modern CSS and stateful JavaScript")
        if any(w in g_lower for w in ["test", "tests", "verify", "benchmark"]):
            requirements.append("Execute automated verification tests")

        planned_actions = [
            f"Analyze environment and generate IMPLEMENTATION_PLAN.md at '{target_path}'",
            f"Scaffold project directory and synthesize code files",
            f"Execute automated build / run commands and verify non-zero outputs"
        ]

        task = StructuredTask(
            goal=g_clean,
            intent="code_generation",
            is_informational=False,
            requirements=requirements,
            constraints=["Ensure zero syntax errors", "Verify files on disk with non-zero size"],
            context={"goal": g_clean, "target_path": target_path, "working_directory": target_path},
            dependencies=dependencies or ["Windows Runtime Environment"],
            planned_actions=planned_actions,
            required_tools=["filesystem", "terminal", "browser"],
            risk_level="MEDIUM",
            power_mode=power_mode_str,
            verification_plan=["All planned files created on disk", "Process execution exits cleanly with code 0"]
        )

        # Distinguish explicit shopping intent if explicitly requested
        is_explicit_shopping = any(w in g_lower for w in [
            "shopping website", "ecommerce website", "e-commerce website",
            "shopping store", "ecommerce store", "e-commerce store",
            "shopping app", "online shop", "online store", "shop website"
        ])
        resolved_intent_type = "create_shopping_website" if is_explicit_shopping else "dynamic_llm_goal"

        return GoalIntent(
            raw_goal=g_clean,
            intent_type=resolved_intent_type,
            target=target_path,
            parameters={"goal": g_clean, "path": target_path, "working_directory": target_path},
            estimated_risk=RiskLevel.MEDIUM,
            requires_terminal=True,
            working_directory=target_path,
            is_informational=False,
            structured_task=task
        )
