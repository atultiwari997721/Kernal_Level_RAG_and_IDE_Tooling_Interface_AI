"""Planning Engine for Decomposing Goals into Structured Executable Plans."""
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from core.goal_engine.engine import GoalIntent


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

        if intent.intent_type == "create_folder":
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

        else:
            # Fallback single step
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
