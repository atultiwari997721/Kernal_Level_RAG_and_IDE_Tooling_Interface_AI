"""Planning Engine for Decomposing Goals into Structured Executable Plans."""
import os
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from core.goal_engine.engine import GoalIntent
from core.planner.templates import CALCULATOR_BAT, CALCULATOR_HTML, CALCULATOR_PY


class PlanStep(BaseModel):
    """Single executable step in a KritiAI plan."""
    id: str
    step_index: int
    objective: str
    agent: str
    tool: str
    input_data: Dict[str, Any]
    expected_result: str
    verification_condition: str
    failure_strategy: str = "retry"
    status: str = "pending"  # pending, in_progress, completed, failed
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ExecutionPlan(BaseModel):
    """Complete structured plan for a goal."""
    task_id: str
    goal: str
    steps: List[PlanStep]


class Planner:
    """Converts GoalIntent into an ordered sequence of verifiable PlanSteps."""

    @staticmethod
    def create_plan(task_id: str, intent: GoalIntent) -> ExecutionPlan:
        steps: List[PlanStep] = []

        # 1. Media / YouTube Playback
        if intent.intent_type == "play_youtube":
            query = intent.parameters.get("query", intent.target)
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Open YouTube and play '{query}'",
                    agent="BrowserAgent",
                    tool="browser",
                    input_data={"operation": "play_youtube", "query": query},
                    expected_result=f"YouTube opened and video/song '{query}' playing in browser",
                    verification_condition="Browser process active and YouTube URL dispatched",
                    failure_strategy="retry"
                )
            )

        # 2. Specific Location Calculator App Creation
        elif intent.intent_type == "create_calculator":
            target_dir = intent.parameters["path"]
            html_path = os.path.join(target_dir, "calculator.html")
            py_path = os.path.join(target_dir, "calculator.py")
            bat_path = os.path.join(target_dir, "run_calculator.bat")

            # Step 0: Create project directory
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Create calculator project directory at '{target_dir}'",
                    agent="FileSystemAgent",
                    tool="filesystem",
                    input_data={"operation": "create_folder", "path": target_dir},
                    expected_result=f"Directory '{target_dir}' created on filesystem",
                    verification_condition=f"os.path.isdir('{target_dir}') is True",
                    failure_strategy="retry"
                )
            )

            # Step 1: Write modern responsive calculator.html
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=1,
                    objective="Generate modern responsive web calculator (calculator.html)",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": html_path, "content": CALCULATOR_HTML},
                    expected_result="calculator.html created with interactive buttons and calculation engine",
                    verification_condition=f"os.path.isfile('{html_path}') and os.path.getsize('{html_path}') > 500",
                    failure_strategy="retry"
                )
            )

            # Step 2: Write Python Tkinter GUI calculator.py
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=2,
                    objective="Generate Python desktop GUI calculator (calculator.py)",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": py_path, "content": CALCULATOR_PY},
                    expected_result="calculator.py created with Tkinter GUI layout and event listeners",
                    verification_condition=f"os.path.isfile('{py_path}') and os.path.getsize('{py_path}') > 300",
                    failure_strategy="retry"
                )
            )

            # Step 3: Write 1-click launcher run_calculator.bat
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=3,
                    objective="Create 1-click Windows launcher (run_calculator.bat)",
                    agent="FileSystemAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": bat_path, "content": CALCULATOR_BAT},
                    expected_result="run_calculator.bat created and ready to execute",
                    verification_condition=f"os.path.isfile('{bat_path}') is True",
                    failure_strategy="retry"
                )
            )

            # Step 4: Open preview so user sees the working calculator immediately
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=4,
                    objective="Open created calculator in browser for live preview",
                    agent="BrowserAgent",
                    tool="browser",
                    input_data={"operation": "open_url", "url": f"file:///{html_path.replace(os.sep, '/')}"},
                    expected_result="Interactive calculator displayed on screen",
                    verification_condition="Browser preview launched",
                    failure_strategy="retry"
                )
            )

        # 3. Web Search
        elif intent.intent_type == "search_web":
            search_query = intent.parameters.get("query", intent.target)
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Search the web for '{search_query}'",
                    agent="BrowserAgent",
                    tool="browser",
                    input_data={"operation": "search_web", "query": search_query},
                    expected_result=f"Web search results displayed for '{search_query}'",
                    verification_condition="Search results opened in browser",
                    failure_strategy="retry"
                )
            )

        # 4. Folder Creation
        elif intent.intent_type == "create_folder":
            target_path = intent.parameters["path"]
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Create folder '{target_path}'",
                    agent="FileSystemAgent",
                    tool="filesystem",
                    input_data={"operation": "create_folder", "path": target_path},
                    expected_result="Folder created on filesystem",
                    verification_condition=f"os.path.isdir('{target_path}') is True",
                    failure_strategy="retry"
                )
            )

        # 5. File Creation
        elif intent.intent_type == "create_file":
            target_path = intent.parameters["path"]
            content = intent.parameters.get("content", "")
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Write file '{target_path}'",
                    agent="FileSystemAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": target_path, "content": content},
                    expected_result="File written and verified",
                    verification_condition=f"os.path.isfile('{target_path}') is True",
                    failure_strategy="retry"
                )
            )

        # 6. Application Launch
        elif intent.intent_type == "launch_app":
            app_name = intent.parameters["app_name"]
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Launch application '{app_name}'",
                    agent="WindowsAgent",
                    tool="app_manager",
                    input_data={"action": "launch", "app_name": app_name},
                    expected_result=f"Application '{app_name}' launched",
                    verification_condition=f"Process '{app_name}' is running",
                    failure_strategy="retry"
                )
            )

        # 7. System Telemetry
        elif intent.intent_type == "system_info":
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective="Inspect Windows hardware and system telemetry",
                    agent="WindowsAgent",
                    tool="system_info",
                    input_data={"detailed": True},
                    expected_result="System telemetry returned",
                    verification_condition="Telemetry data present",
                    failure_strategy="retry"
                )
            )

        # 8. Terminal Command
        elif intent.intent_type == "terminal_command":
            cmd = intent.parameters["command"]
            workdir = intent.parameters.get("working_directory")
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Execute command: {cmd}",
                    agent="CodingAgent",
                    tool="powershell",
                    input_data={"command": cmd, "working_directory": workdir},
                    expected_result="Process exited with code 0",
                    verification_condition="exit_code == 0",
                    failure_strategy="retry"
                )
            )

        # 9. Fallback
        else:
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Execute task: {intent.raw_goal}",
                    agent="FileSystemAgent",
                    tool="filesystem",
                    input_data={"operation": "search", "path": intent.working_directory, "pattern": "*"},
                    expected_result="Workspace inspected",
                    verification_condition="Inspection successful",
                    failure_strategy="ask_user"
                )
            )

        return ExecutionPlan(task_id=task_id, goal=intent.raw_goal, steps=steps)
