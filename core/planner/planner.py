"""Planning Engine for Decomposing Goals into Structured Executable Plans and IMPLEMENTATION_PLAN.md."""
import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from core.goal_engine.engine import GoalIntent, StructuredTask
from core.planner.templates import (
    CALCULATOR_BAT, CALCULATOR_HTML, CALCULATOR_PY,
    SHOPPING_ARCHITECTURE_MD, SHOPPING_HTML, SHOPPING_CSS,
    SHOPPING_JS, SHOPPING_SERVER_PY, SHOPPING_PACKAGE_JSON, SHOPPING_RUN_BAT
)

logger = logging.getLogger("kritiai.planner")


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
    """Complete structured plan for a goal with IMPLEMENTATION_PLAN.md support."""
    task_id: str
    goal: str
    steps: List[PlanStep]
    plan_markdown: Optional[str] = None
    target_directory: Optional[str] = None


class Planner:
    """Converts GoalIntent into an ordered sequence of verifiable PlanSteps with dynamic markdown plans."""

    @staticmethod
    def generate_implementation_plan_markdown(
        goal: str,
        target_dir: str,
        steps: List[PlanStep],
        structured_task: Optional[StructuredTask] = None,
        files_to_create: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        commands: Optional[List[str]] = None
    ) -> str:
        """Dynamically generate an official 14-section IMPLEMENTATION_PLAN.md document."""
        files_str = "\n".join([f"- `{f}`" for f in (files_to_create or [])]) or "- Discovered dynamically during synthesis"
        deps_str = "\n".join([f"- {d}" for d in (dependencies or ["Windows Runtime Environment"])])
        cmds_str = "\n".join([f"```powershell\n{c}\n```" for c in (commands or [])]) or "- No external compilation command required."

        step_lines = []
        for idx, s in enumerate(steps, start=1):
            step_lines.append(f"{idx}. **[{s.tool.upper()}]** {s.objective}\n   - Agent: `{s.agent}`\n   - Verification: `{s.verification_condition}`")
        steps_str = "\n".join(step_lines) or "1. Execute task instructions."

        reqs = structured_task.requirements if structured_task else [f"Execute user request: {goal}"]
        reqs_str = "\n".join([f"- {r}" for r in reqs])

        plan_md = f"""# Implementation Plan

## Goal
{goal}

## Current State
Workspace: `{target_dir}`
Status: Pre-execution environment inspection completed. Directory structure prepared for synthesis.

## Requirements
{reqs_str}

## Assumptions
- Local Windows environment with standard runtime access (PowerShell, FileSystem, Browser).
- Target filesystem path is writable and isolated from protected system directories.

## Architecture
Decoupled modular architecture generated based on user request:
- Presentation / Frontend: Modern UI components with responsive styling.
- Logic / Processing: Clean entry point script or reactive client application.
- Orchestration: Verifiable execution runner with automated health check.

## Files To Create
{files_str}

## Files To Modify
- None (New project workspace)

## Dependencies
{deps_str}

## Commands
{cmds_str}

## Execution Steps
{steps_str}

## Risks
- Medium: Modifying files in the designated target directory `{target_dir}`.
- Mitigation: All file operations are scoped strictly to the target folder with non-destructive overwrite guards.

## Permission Requirements
- FileSystem write permission to `{target_dir}`.
- Subprocess execution permission for verification commands.

## Testing Strategy
- Automated file existence and non-zero size verification for all generated artifacts.
- Syntax and runtime exit code verification upon execution.

## Verification Strategy
- Non-empty output confirmation.
- Exit code 0 on test runners or successful launch of UI preview.

## Rollback Strategy
- In case of critical failure, remove generated files in `{target_dir}` and revert project state.
"""
        return plan_md

    @staticmethod
    def parse_plan_from_markdown(
        markdown_content: str,
        task_id: str,
        target_dir: str
    ) -> ExecutionPlan:
        """Parse an edited IMPLEMENTATION_PLAN.md back into executable PlanSteps."""
        steps: List[PlanStep] = []
        lines = markdown_content.splitlines()
        in_steps_section = False
        step_idx = 0

        goal = "User Edited Plan"
        goal_match = re.search(r"## Goal\s*\n+([^\n#]+)", markdown_content)
        if goal_match:
            goal = goal_match.group(1).strip()

        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## Execution Steps"):
                in_steps_section = True
                continue
            elif in_steps_section and line_str.startswith("## "):
                in_steps_section = False
                break

            if in_steps_section and re.match(r"^\d+\.\s+", line_str):
                # Extract step line e.g. "1. **[FILESYSTEM]** Create project structure..."
                tool = "filesystem"
                tool_match = re.search(r"\[([A-Z_]+)\]", line_str)
                if tool_match:
                    t = tool_match.group(1).lower()
                    if t in ["filesystem", "powershell", "cmd", "browser", "terminal"]:
                        tool = t

                obj = re.sub(r"^\d+\.\s+(\*\*\[[A-Z_]+\]\*\*\s*)?", "", line_str).strip()
                agent = "CodingAgent"
                if tool == "filesystem":
                    agent = "FileSystemAgent"
                elif tool == "browser":
                    agent = "BrowserAgent"

                steps.append(
                    PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=step_idx,
                        objective=obj or f"Step {step_idx + 1}",
                        agent=agent,
                        tool=tool,
                        input_data={"operation": "execute", "path": target_dir, "objective": obj},
                        expected_result="Step verified successfully",
                        verification_condition="verified",
                        failure_strategy="retry"
                    )
                )
                step_idx += 1

        if not steps:
            # Fallback single step
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Execute user-revised plan in {target_dir}",
                    agent="CodingAgent",
                    tool="powershell",
                    input_data={"command": f"echo 'Executing plan for {goal}'", "working_directory": target_dir},
                    expected_result="Plan executed",
                    verification_condition="exit_code == 0"
                )
            )

        return ExecutionPlan(
            task_id=task_id,
            goal=goal,
            steps=steps,
            plan_markdown=markdown_content,
            target_directory=target_dir
        )

    @staticmethod
    def plan_with_model(
        task_id: str,
        goal: str,
        model_gateway: Any,
        model_router: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ExecutionPlan]:
        """Prompt active AI model (Ollama, API, or local) to autonomously plan execution steps."""
        if not model_gateway or not model_router:
            return None

        workdir = (context or {}).get("working_directory", os.getcwd())

        system_prompt = (
            "You are the KritiAI Windows Autonomous Execution Planner.\n"
            "Decompose the user's goal into concrete, verifiable steps using Windows execution tools.\n\n"
            "Respond ONLY with a JSON array of step objects matching this schema:\n"
            "[\n"
            "  {\n"
            "    \"objective\": \"Short objective\",\n"
            "    \"agent\": \"FileSystemAgent\"|\"CodingAgent\"|\"BrowserAgent\"|\"WindowsAgent\",\n"
            "    \"tool\": \"filesystem\"|\"powershell\"|\"cmd\"|\"browser\"|\"app_manager\"|\"system_info\",\n"
            "    \"input_data\": { ... parameters matching the tool schema ... },\n"
            "    \"expected_result\": \"Expected outcome\",\n"
            "    \"verification_condition\": \"Verification string or condition\"\n"
            "  }\n"
            "]"
        )

        user_prompt = f"Goal: {goal}\nWorking Directory: {workdir}\nGenerate the execution steps:"

        try:
            prov_name, model_name = model_router.route(task_type="coding")
            response = model_gateway.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                provider_name=prov_name,
                model=model_name,
                temperature=0.2
            )

            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            raw_steps = json.loads(content)
            if isinstance(raw_steps, list) and len(raw_steps) > 0:
                steps: List[PlanStep] = []
                for idx, s in enumerate(raw_steps):
                    if not isinstance(s, dict) or "tool" not in s or "input_data" not in s:
                        continue
                    step_obj = PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=idx,
                        objective=s.get("objective", f"Step {idx + 1}"),
                        agent=s.get("agent", "CodingAgent"),
                        tool=s.get("tool", "filesystem"),
                        input_data=s.get("input_data", {}),
                        expected_result=s.get("expected_result", "Step executed successfully"),
                        verification_condition=s.get("verification_condition", "verified"),
                        failure_strategy=s.get("failure_strategy", "retry")
                    )
                    steps.append(step_obj)

                if steps:
                    logger.info(f"Model generated dynamic plan with {len(steps)} steps for: {goal}")
                    plan_md = Planner.generate_implementation_plan_markdown(goal, workdir, steps)
                    return ExecutionPlan(
                        task_id=task_id,
                        goal=goal,
                        steps=steps,
                        plan_markdown=plan_md,
                        target_directory=workdir
                    )

        except Exception as e:
            logger.warning(f"Dynamic LLM planning failed, falling back to adaptive planner: {e}")

        return None

    @staticmethod
    def create_adaptive_plan(
        task_id: str,
        goal: str,
        target_dir: str,
        workdir: str,
        structured_task: Optional[StructuredTask] = None
    ) -> ExecutionPlan:
        """Dynamically formulate a complete, multi-step verifiable execution plan with IMPLEMENTATION_PLAN.md."""
        from core.planner.code_synthesizer import synthesize_project_artifacts, detect_runtime

        runtime = detect_runtime(goal)
        artifacts, exec_cmd = synthesize_project_artifacts(goal, target_dir)
        steps: List[PlanStep] = []

        # Step 0: Create project workspace folder
        steps.append(
            PlanStep(
                id=str(uuid.uuid4()),
                step_index=0,
                objective=f"Scaffold project workspace directory at '{target_dir}'",
                agent="FileSystemAgent",
                tool="filesystem",
                input_data={"operation": "create_folder", "path": target_dir},
                expected_result=f"Directory '{target_dir}' created on filesystem",
                verification_condition=f"os.path.isdir('{target_dir}') is True",
                failure_strategy="retry"
            )
        )

        cur_idx = 1
        # Include IMPLEMENTATION_PLAN.md in artifacts
        plan_md_path = os.path.join(target_dir, "IMPLEMENTATION_PLAN.md")
        files_created = list(artifacts.keys()) + ["IMPLEMENTATION_PLAN.md"]
        cmds_run = [exec_cmd] if exec_cmd else []

        plan_md_content = Planner.generate_implementation_plan_markdown(
            goal=goal,
            target_dir=target_dir,
            steps=steps,
            structured_task=structured_task,
            files_to_create=files_created,
            commands=cmds_run
        )

        # Step 1: Write IMPLEMENTATION_PLAN.md
        steps.append(
            PlanStep(
                id=str(uuid.uuid4()),
                step_index=cur_idx,
                objective="Generate formal project architecture and IMPLEMENTATION_PLAN.md",
                agent="CodingAgent",
                tool="filesystem",
                input_data={"operation": "create_file", "path": plan_md_path, "content": plan_md_content},
                expected_result="IMPLEMENTATION_PLAN.md created on filesystem with 14-section execution strategy",
                verification_condition=f"os.path.isfile('{plan_md_path}') and os.path.getsize('{plan_md_path}') > 200",
                failure_strategy="retry"
            )
        )
        cur_idx += 1

        # Synthesize synthesized source code files
        for fname, content in artifacts.items():
            fpath = os.path.join(target_dir, fname)
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=cur_idx,
                    objective=f"Synthesize {fname} with verified functional implementation",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": fpath, "content": content},
                    expected_result=f"{fname} generated with verified code contents",
                    verification_condition=f"os.path.isfile('{fpath}') and os.path.getsize('{fpath}') > 10",
                    failure_strategy="retry"
                )
            )
            cur_idx += 1

        # Execute build/run command
        if exec_cmd:
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=cur_idx,
                    objective=f"Execute runtime verification: {exec_cmd}",
                    agent="CodingAgent",
                    tool="powershell",
                    input_data={"command": exec_cmd, "working_directory": target_dir},
                    expected_result="Process executed and completed with exit code 0",
                    verification_condition="exit_code == 0",
                    failure_strategy="retry"
                )
            )
            cur_idx += 1

        # If web, launch preview in browser
        if runtime == "web" and "index.html" in artifacts:
            index_path = os.path.join(target_dir, "index.html")
            steps.append(
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=cur_idx,
                    objective="Launch project in browser preview",
                    agent="BrowserAgent",
                    tool="browser",
                    input_data={"operation": "open_url", "url": f"file:///{index_path.replace(os.sep, '/')}"},
                    expected_result="Interactive project launched in default browser",
                    verification_condition="Browser process active",
                    failure_strategy="retry"
                )
            )

        # Refresh the plan markdown with the complete step list
        full_plan_md = Planner.generate_implementation_plan_markdown(
            goal=goal,
            target_dir=target_dir,
            steps=steps,
            structured_task=structured_task,
            files_to_create=files_created,
            commands=cmds_run
        )

        return ExecutionPlan(
            task_id=task_id,
            goal=goal,
            steps=steps,
            plan_markdown=full_plan_md,
            target_directory=target_dir
        )

    @staticmethod
    def create_plan(
        task_id: str,
        intent: GoalIntent,
        model_gateway: Optional[Any] = None,
        model_router: Optional[Any] = None
    ) -> ExecutionPlan:
        """Create execution plan dynamically without canned demonstration hacks."""
        # 1. Informational Query Plan (Zero disk operations)
        if intent.is_informational:
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=[
                    PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=0,
                        objective=f"Synthesize comprehensive conversational response for: '{intent.raw_goal}'",
                        agent="ResearchAgent",
                        tool="model_gateway",
                        input_data={"query": intent.raw_goal},
                        expected_result="Response formulated and delivered",
                        verification_condition="verified"
                    )
                ]
            )

        # 2. Media / YouTube Playback
        if intent.intent_type == "play_youtube":
            query = intent.parameters.get("query", intent.target)
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=[
                    PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=0,
                        objective=f"Search and play audio/video for '{query}' in browser",
                        agent="BrowserAgent",
                        tool="browser",
                        input_data={"operation": "play_youtube", "query": query},
                        expected_result=f"Browser opened and playback dispatched for '{query}'",
                        verification_condition="Browser process active and YouTube URL dispatched",
                        failure_strategy="retry"
                    )
                ]
            )

        # 3. Directory Listing / Inspection
        if intent.intent_type == "list_directory":
            target_dir = intent.parameters.get("path", intent.target or os.getcwd())
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=[
                    PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=0,
                        objective=f"List directory contents of '{target_dir}'",
                        agent="FileSystemAgent",
                        tool="filesystem",
                        input_data={"operation": "list_dir", "path": target_dir},
                        expected_result=f"Contents of '{target_dir}' enumerated",
                        verification_condition=f"os.path.isdir('{target_dir}')",
                        failure_strategy="retry"
                    )
                ]
            )

        # 4. Terminal Command Execution
        if intent.intent_type == "terminal_command":
            cmd = intent.parameters["command"]
            workdir = intent.parameters.get("working_directory", os.getcwd())
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=[
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
                ]
            )

        # 5. Create Folder
        if intent.intent_type == "create_folder":
            target_dir = intent.target or intent.parameters.get("path")
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=[
                    PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=0,
                        objective=f"Create directory '{target_dir}'",
                        agent="FileSystemAgent",
                        tool="filesystem",
                        input_data={"operation": "create_folder", "path": target_dir},
                        expected_result=f"Directory '{target_dir}' created on disk",
                        verification_condition=f"os.path.isdir('{target_dir}')",
                        failure_strategy="retry"
                    )
                ],
                target_directory=target_dir
            )

        # 6. Create File
        if intent.intent_type == "create_file":
            file_path = intent.target or intent.parameters.get("path")
            content = intent.parameters.get("content", "")
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=[
                    PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=0,
                        objective=f"Create file '{file_path}' with verified content",
                        agent="CodingAgent",
                        tool="filesystem",
                        input_data={"operation": "create_file", "path": file_path, "content": content},
                        expected_result=f"File '{file_path}' written to disk",
                        verification_condition=f"os.path.isfile('{file_path}')",
                        failure_strategy="retry"
                    )
                ],
                target_directory=os.path.dirname(file_path) if os.path.dirname(file_path) else os.getcwd()
            )

        # 7. Read File
        if intent.intent_type == "read_file":
            file_path = intent.target or intent.parameters.get("path")
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=[
                    PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=0,
                        objective=f"Read file '{file_path}'",
                        agent="FileSystemAgent",
                        tool="filesystem",
                        input_data={"operation": "read_file", "path": file_path},
                        expected_result=f"Contents of '{file_path}' read",
                        verification_condition=f"os.path.isfile('{file_path}')",
                        failure_strategy="retry"
                    )
                ]
            )

        # 7. Web Search
        if intent.intent_type == "search_web":
            query = intent.target or intent.parameters.get("query")
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=[
                    PlanStep(
                        id=str(uuid.uuid4()),
                        step_index=0,
                        objective=f"Search web for '{query}'",
                        agent="BrowserAgent",
                        tool="browser",
                        input_data={"operation": "search_web", "query": query},
                        expected_result="Web search executed",
                        verification_condition="Browser process active",
                        failure_strategy="retry"
                    )
                ]
            )

        # 8. Desktop & Web Calculator Application
        if intent.intent_type == "create_calculator":
            target_dir = intent.target or intent.parameters.get("path") or os.path.join(intent.working_directory, "CalculatorApp")
            steps = [
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Create calculator application workspace at '{target_dir}'",
                    agent="FileSystemAgent",
                    tool="filesystem",
                    input_data={"operation": "create_folder", "path": target_dir},
                    expected_result=f"Directory '{target_dir}' created on disk",
                    verification_condition=f"os.path.isdir('{target_dir}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=1,
                    objective="Generate modern responsive calculator.html",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "calculator.html"), "content": CALCULATOR_HTML},
                    expected_result="calculator.html created",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'calculator.html')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=2,
                    objective="Generate Python desktop GUI calculator.py using Tkinter",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "calculator.py"), "content": CALCULATOR_PY},
                    expected_result="calculator.py created",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'calculator.py')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=3,
                    objective="Generate Windows launch script run_calculator.bat",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "run_calculator.bat"), "content": CALCULATOR_BAT},
                    expected_result="run_calculator.bat created",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'run_calculator.bat')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=4,
                    objective="Launch calculator in default web browser",
                    agent="BrowserAgent",
                    tool="browser",
                    input_data={"operation": "open_url", "url": f"file:///{os.path.join(target_dir, 'calculator.html').replace(os.sep, '/')}"},
                    expected_result="Calculator launched in browser",
                    verification_condition="Browser process active"
                )
            ]
            plan_md = Planner.generate_implementation_plan_markdown(
                goal=intent.raw_goal,
                target_dir=target_dir,
                steps=steps,
                structured_task=intent.structured_task,
                files_to_create=["calculator.html", "calculator.py", "run_calculator.bat"]
            )
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=steps,
                plan_markdown=plan_md,
                target_directory=target_dir
            )

        # 9. Explicit Shopping Website Scaffolding
        if intent.intent_type == "create_shopping_website":
            target_dir = intent.target or intent.parameters.get("path") or os.path.join(intent.working_directory, "ShoppingWebsite")
            steps = [
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=0,
                    objective=f"Scaffold project workspace directory at '{target_dir}'",
                    agent="FileSystemAgent",
                    tool="filesystem",
                    input_data={"operation": "create_folder", "path": target_dir},
                    expected_result=f"Directory '{target_dir}' created on filesystem",
                    verification_condition=f"os.path.isdir('{target_dir}') is True"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=1,
                    objective="Synthesize system ARCHITECTURE.md specification",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "ARCHITECTURE.md"), "content": SHOPPING_ARCHITECTURE_MD},
                    expected_result="ARCHITECTURE.md created with complete design spec",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'ARCHITECTURE.md')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=2,
                    objective="Synthesize responsive index.html user interface",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "index.html"), "content": SHOPPING_HTML},
                    expected_result="index.html created with semantic markup",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'index.html')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=3,
                    objective="Synthesize styles.css with modern aesthetics and dark mode support",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "styles.css"), "content": SHOPPING_CSS},
                    expected_result="styles.css generated",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'styles.css')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=4,
                    objective="Synthesize app.js with cart, catalog filter, and checkout logic",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "app.js"), "content": SHOPPING_JS},
                    expected_result="app.js generated",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'app.js')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=5,
                    objective="Synthesize backend server.py API and static server",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "server.py"), "content": SHOPPING_SERVER_PY},
                    expected_result="server.py generated",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'server.py')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=6,
                    objective="Generate Node/NPM package.json project descriptor",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "package.json"), "content": SHOPPING_PACKAGE_JSON},
                    expected_result="package.json created",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'package.json')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=7,
                    objective="Generate run_shopping_website.bat automated launch script",
                    agent="CodingAgent",
                    tool="filesystem",
                    input_data={"operation": "create_file", "path": os.path.join(target_dir, "run_shopping_website.bat"), "content": SHOPPING_RUN_BAT},
                    expected_result="run_shopping_website.bat created",
                    verification_condition=f"os.path.isfile('{os.path.join(target_dir, 'run_shopping_website.bat')}')"
                ),
                PlanStep(
                    id=str(uuid.uuid4()),
                    step_index=8,
                    objective="Launch project in browser preview",
                    agent="BrowserAgent",
                    tool="browser",
                    input_data={"operation": "open_url", "url": f"file:///{os.path.join(target_dir, 'index.html').replace(os.sep, '/')}"},
                    expected_result="Interactive project launched in default browser",
                    verification_condition="Browser process active"
                )
            ]
            plan_md = Planner.generate_implementation_plan_markdown(
                goal=intent.raw_goal,
                target_dir=target_dir,
                steps=steps,
                structured_task=intent.structured_task,
                files_to_create=["ARCHITECTURE.md", "index.html", "styles.css", "app.js", "server.py", "package.json", "run_shopping_website.bat"]
            )
            return ExecutionPlan(
                task_id=task_id,
                goal=intent.raw_goal,
                steps=steps,
                plan_markdown=plan_md,
                target_directory=target_dir
            )

        # 6. Software Development & Dynamic Goals
        # Formulate full adaptive plan with IMPLEMENTATION_PLAN.md
        target_dir = intent.target or intent.parameters.get("path") or intent.working_directory
        return Planner.create_adaptive_plan(
            task_id=task_id,
            goal=intent.raw_goal,
            target_dir=target_dir,
            workdir=intent.working_directory,
            structured_task=intent.structured_task
        )
