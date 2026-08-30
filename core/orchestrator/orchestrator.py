"""Central AI Orchestrator for KritiAI."""
import logging
from typing import Any, Callable, Dict, List, Optional

from agents.manager import AgentManager
from ai.gateway.gateway import ModelGateway
from ai.router.router import ModelRouter
from config.settings import AppConfig, PowerMode, get_config
from core.goal_engine.engine import GoalEngine, GoalIntent
from core.planner.planner import ExecutionPlan, PlanStep, Planner
from core.recovery.recovery import SelfCorrectionEngine
from core.state_machine.states import TaskState
from core.task_engine.engine import TaskEngine
from core.verification.verifier import VerificationEngine
from memory.base import MemoryTier
from memory.manager import MemoryManager
from security.permissions.engine import PermissionEngine
from security.policies.models import PermissionDecision
from security.sandbox.watchdog import get_emergency_stop_manager
from tools.registry import ToolRegistry

logger = logging.getLogger("kritiai.orchestrator")


class AIOrchestrator:
    """Coordinates Goal Understanding, Memory, Planning, Policy, Tools, Verification, and Self-Correction."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        task_engine: Optional[TaskEngine] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory_manager: Optional[MemoryManager] = None,
        model_gateway: Optional[ModelGateway] = None,
        model_router: Optional[ModelRouter] = None,
        agent_manager: Optional[AgentManager] = None,
        goal_engine: Optional[GoalEngine] = None
    ):
        self.config = config or get_config()
        self.task_engine = task_engine or TaskEngine()
        self.tool_registry = tool_registry or ToolRegistry(self.config)
        self.memory_manager = memory_manager or MemoryManager()
        self.model_gateway = model_gateway or ModelGateway(self.config)
        self.model_router = model_router or ModelRouter(self.model_gateway, self.config)
        self.agent_manager = agent_manager or AgentManager()
        self.goal_engine = goal_engine or GoalEngine(str(self.config.workspace_dir))
        self.verification_engine = VerificationEngine()
        self.self_correction = SelfCorrectionEngine()
        self._active_tasks: Dict[str, Dict[str, Any]] = {}

    def run_goal(
        self,
        goal: str,
        session_id: Optional[str] = None,
        power_mode: Optional[PowerMode] = None,
        step_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Execute a goal end-to-end autonomously according to active Power Mode."""
        active_power = power_mode or self.config.power_mode
        stop_mgr = get_emergency_stop_manager()

        # Check emergency stop before starting
        if stop_mgr.is_stopped:
            return {
                "success": False,
                "error": "Cannot execute: Emergency STOP is active.",
                "status": TaskState.CANCELLED.value
            }

        # 1. Initialize Task
        task = self.task_engine.create_task(
            goal=goal,
            session_id=session_id,
            mode="kritimode",
            power_mode=active_power.value
        )
        task_id = task["id"]

        try:
            # 2. Understand
            self.task_engine.set_state(task_id, TaskState.UNDERSTANDING)
            intent = self.goal_engine.understand_goal(goal, context={"working_directory": str(self.config.workspace_dir), "power_mode": active_power.value}, memory_manager=self.memory_manager)

            # 2b. Handle Informational / Conversational Queries (No filesystem mutation)
            if intent.is_informational:
                self.task_engine.set_state(task_id, TaskState.EXECUTING)
                prov_name, mod_name = self.model_router.route(task_type="general", power_mode=active_power.value)
                messages = [
                    {"role": "system", "content": "You are KritiAI, an intelligent local-first Windows execution assistant. Provide helpful, comprehensive, and clear answers."},
                    {"role": "user", "content": goal}
                ]
                resp = self.model_gateway.generate(messages, provider_name=prov_name, model=mod_name)
                answer = resp.content.strip()

                self.task_engine.repo.update_task(
                    task_id,
                    status=TaskState.COMPLETED.value,
                    final_result=answer,
                    active_model=f"{prov_name}/{mod_name}",
                    active_agent="ResearchAgent",
                    active_tool="model_gateway"
                )
                self.task_engine.set_state(task_id, TaskState.COMPLETED)

                if step_callback:
                    step_callback({
                        "event": "task_completed",
                        "task_id": task_id,
                        "result": answer,
                        "is_informational": True,
                        "active_model": f"{prov_name}/{mod_name}"
                    })

                return {
                    "success": True,
                    "task_id": task_id,
                    "status": TaskState.COMPLETED.value,
                    "final_result": answer,
                    "is_informational": True,
                    "active_model": f"{prov_name}/{mod_name}",
                    "structured_task": intent.structured_task.model_dump() if intent.structured_task else None
                }

            # 3. Remember
            memories = self.memory_manager.recall(goal, top_k=3)
            memory_summary = [m.content for m in memories]

            # 4. Plan
            self.task_engine.set_state(task_id, TaskState.PLANNING)
            plan = Planner.create_plan(
                task_id,
                intent,
                model_gateway=self.model_gateway,
                model_router=self.model_router
            )
            self.task_engine.attach_plan(task_id, plan)

            # 5. Route Model & Select Agents
            provider_name, model_name = self.model_router.route(
                task_type="coding" if intent.requires_terminal else "general",
                power_mode=active_power.value
            )
            primary_agent = self.agent_manager.select_agent_for_goal(goal)

            self.task_engine.repo.update_task(
                task_id,
                active_agent=primary_agent.name,
                active_model=f"{provider_name}/{model_name}",
                active_tool=plan.steps[0].tool if plan.steps else "none"
            )

            if step_callback:
                step_callback({
                    "event": "plan_created",
                    "task_id": task_id,
                    "plan": [s.model_dump() for s in plan.steps],
                    "plan_markdown": plan.plan_markdown,
                    "structured_task": intent.structured_task.model_dump() if intent.structured_task else None
                })

            # 6. Execute Steps
            self.task_engine.set_state(task_id, TaskState.EXECUTING)
            observations: List[str] = []
            self._active_tasks[task_id] = {
                "plan": plan,
                "intent": intent,
                "observations": observations,
                "goal": goal,
                "active_power": active_power,
                "current_step": 0
            }

            for step_idx, step in enumerate(plan.steps):
                if stop_mgr.is_stopped:
                    self.task_engine.set_state(task_id, TaskState.CANCELLED, reason="Emergency STOP pressed during execution.")
                # Ensure task state is EXECUTING for this step
                curr_task = self.task_engine.get_task(task_id)
                if curr_task and curr_task["status"] != TaskState.EXECUTING.value:
                    self.task_engine.set_state(task_id, TaskState.EXECUTING)

                step.status = "in_progress"
                self.task_engine.repo.update_task(
                    task_id,
                    current_step=step_idx,
                    active_agent=step.agent,
                    active_tool=step.tool
                )

                if step_callback:
                    step_callback({"event": "step_started", "task_id": task_id, "step": step.model_dump()})

                # Check policy for this step
                tool = self.tool_registry.get_tool(step.tool)
                if not tool:
                    step.status = "failed"
                    step.error_message = f"Tool {step.tool} not registered."
                    self.task_engine.set_state(task_id, TaskState.FAILED)
                    return {"success": False, "task_id": task_id, "error": step.error_message}

                # Execute with retry loop
                retries = 0
                step_success = False
                max_retries = self.config.max_retries

                while retries <= max_retries and not step_success:
                    if stop_mgr.is_stopped:
                        self.task_engine.set_state(task_id, TaskState.CANCELLED)
                        return {"success": False, "task_id": task_id, "status": TaskState.CANCELLED.value}

                    # Execute tool through Registry (handles PermissionEngine, Watchdog, and Audit Logging)
                    tool_output = self.tool_registry.execute_tool(
                        tool_name=step.tool,
                        parameters=step.input_data,
                        task_id=task_id,
                        agent_name=step.agent,
                        power_mode=active_power
                    )

                    # Check if permission engine requested approval
                    if tool_output.get("decision") == PermissionDecision.ASK_USER.value:
                        self.task_engine.set_state(task_id, TaskState.WAITING_FOR_APPROVAL, reason="Permission Engine requested user approval")
                        self._active_tasks[task_id]["current_step"] = step_idx
                        return {
                            "success": False,
                            "task_id": task_id,
                            "status": TaskState.WAITING_FOR_APPROVAL.value,
                            "approval_required": True,
                            "prompt": tool_output.get("prompt") or f"Permission required to execute '{step.objective}' using tool '{step.tool}'.",
                            "step": step.model_dump(),
                            "tool_name": step.tool,
                            "action": step.input_data.get("operation") or step.objective
                        }

                    # 7. Observe & Verify
                    self.task_engine.set_state(task_id, TaskState.OBSERVING)
                    self.task_engine.set_state(task_id, TaskState.VERIFYING)
                    verif = self.verification_engine.verify_step(tool_output, step.verification_condition)

                    if verif.get("verified", False):
                        step_success = True
                        step.status = "completed"
                        step.output_data = tool_output.get("data")
                        obs_msg = f"Step {step_idx + 1} ({step.objective}): Verified - {verif.get('reason')}"
                        observations.append(obs_msg)
                        break
                    else:
                        # 8. Failure & Recovery Diagnosis
                        retries += 1
                        err = tool_output.get("error") or verif.get("reason", "Verification failed")
                        self.task_engine.set_state(task_id, TaskState.RECOVERING, reason=f"Failure: {err}")
                        
                        rec_plan = self.self_correction.diagnose(
                            error_str=str(err),
                            tool_name=step.tool,
                            parameters=step.input_data,
                            retry_count=retries,
                            max_retries=max_retries
                        )

                        if rec_plan.action == "ask_user":
                            step.status = "failed"
                            step.error_message = rec_plan.message
                            self.task_engine.set_state(task_id, TaskState.WAITING_FOR_USER)
                            return {
                                "success": False,
                                "task_id": task_id,
                                "status": TaskState.WAITING_FOR_USER.value,
                                "error": rec_plan.message
                            }
                        elif rec_plan.action == "alternative_tool" and rec_plan.alternative_tool:
                            step.tool = rec_plan.alternative_tool
                            if rec_plan.adjusted_parameters:
                                step.input_data = rec_plan.adjusted_parameters
                        
                        self.task_engine.repo.update_task(task_id, retries=retries, errors=str(err))
                        self.task_engine.set_state(task_id, TaskState.EXECUTING, reason="Retrying step")

                if not step_success:
                    step.status = "failed"
                    self.task_engine.set_state(task_id, TaskState.FAILED)
                    return {
                        "success": False,
                        "task_id": task_id,
                        "status": TaskState.FAILED.value,
                        "error": f"Failed step: {step.objective}"
                    }

                if step_callback:
                    step_callback({
                        "event": "step_completed",
                        "task_id": task_id,
                        "step": step.model_dump(),
                        "output": step.output_data
                    })

            # 9. Complete Task
            final_report = f"Successfully completed: '{goal}'.\n" + "\n".join(observations)
            self.task_engine.repo.update_task(
                task_id,
                status=TaskState.COMPLETED.value,
                final_result=final_report,
                verification_status="verified",
                observations="\n".join(observations)
            )
            self.task_engine.set_state(task_id, TaskState.COMPLETED)

            # Store in Task Memory
            self.memory_manager.remember(
                tier=MemoryTier.TASK,
                content=f"Goal: {goal} | Result: {final_report}",
                key=f"task_{task_id}",
                metadata={"task_id": task_id, "success": True}
            )

            completion_payload = {
                "event": "task_completed",
                "task_id": task_id,
                "result": final_report,
                "intent_type": intent.intent_type,
                "target": intent.target,
                "parameters": intent.parameters
            }
            if step_callback:
                step_callback(completion_payload)

            return {
                "success": True,
                "task_id": task_id,
                "status": TaskState.COMPLETED.value,
                "final_result": final_report,
                "observations": observations,
                "intent_type": intent.intent_type,
                "target": intent.target,
                "parameters": intent.parameters
            }

        except Exception as ex:
            logger.exception(f"Unhandled error in Orchestrator for task {task_id}")
            self.task_engine.set_state(task_id, TaskState.FAILED, reason=str(ex))
            return {
                "success": False,
                "task_id": task_id,
                "status": TaskState.FAILED.value,
                "error": str(ex)
            }

    def resume_task_after_approval(
        self,
        task_id: str,
        decision: str = "allow_once",
        modified_plan_markdown: Optional[str] = None,
        step_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Resume task execution after user interaction with the Approval Modal or Plan Editor."""
        task_data = self._active_tasks.get(task_id)
        if not task_data:
            return {"success": False, "task_id": task_id, "error": f"Active task data for {task_id} not found."}

        # If user modified IMPLEMENTATION_PLAN.md, re-read and parse it as the new source of truth!
        if modified_plan_markdown:
            target_p = task_data["plan"].target_directory or task_data["intent"].target or str(self.config.workspace_dir)
            updated_plan = Planner.parse_plan_from_markdown(modified_plan_markdown, task_id, target_p)
            task_data["plan"] = updated_plan
            self.task_engine.attach_plan(task_id, updated_plan)

        plan: ExecutionPlan = task_data["plan"]
        intent: GoalIntent = task_data["intent"]
        observations: List[str] = task_data["observations"]
        goal: str = task_data["goal"]
        start_step: int = task_data.get("current_step", 0)

        if decision == "deny":
            self.task_engine.cancel_task(task_id, reason="User denied action approval.")
            if step_callback:
                step_callback({"event": "task_cancelled", "task_id": task_id, "reason": "User denied action."})
            return {"success": False, "task_id": task_id, "status": TaskState.CANCELLED.value, "error": "Action denied by user."}

        if decision == "always_allow":
            step = plan.steps[start_step]
            action_name = step.input_data.get("operation") or step.objective
            self.tool_registry.permission_engine.allow_action_permanently(step.tool, action_name)

        stop_mgr = get_emergency_stop_manager()
        self.task_engine.set_state(task_id, TaskState.EXECUTING)

        try:
            for step_idx in range(start_step, len(plan.steps)):
                step = plan.steps[step_idx]
                if stop_mgr.is_stopped:
                    self.task_engine.set_state(task_id, TaskState.CANCELLED, reason="Emergency STOP pressed.")
                    return {"success": False, "task_id": task_id, "status": TaskState.CANCELLED.value}

                curr_task = self.task_engine.get_task(task_id)
                if curr_task and curr_task["status"] != TaskState.EXECUTING.value:
                    self.task_engine.set_state(task_id, TaskState.EXECUTING)

                step.status = "in_progress"
                self.task_engine.repo.update_task(task_id, current_step=step_idx, active_agent=step.agent, active_tool=step.tool)
                if step_callback:
                    step_callback({"event": "step_started", "task_id": task_id, "step": step.model_dump()})

                # For the approved step, directly execute with bypass
                if step_idx == start_step:
                    tool = self.tool_registry.get_tool(step.tool)
                    if not tool:
                        step.status = "failed"
                        self.task_engine.set_state(task_id, TaskState.FAILED)
                        return {"success": False, "task_id": task_id, "error": f"Tool {step.tool} not registered."}
                    tool_res = tool.execute(**step.input_data)
                    tool_output = {
                        "success": tool_res.success,
                        "data": tool_res.data,
                        "error": tool_res.error,
                        "verification": tool_res.verification,
                        "decision": PermissionDecision.ALLOW.value
                    }
                else:
                    tool_output = self.tool_registry.execute_tool(
                        tool_name=step.tool,
                        parameters=step.input_data,
                        task_id=task_id,
                        agent_name=step.agent,
                        power_mode=task_data.get("active_power")
                    )
                    if tool_output.get("decision") == PermissionDecision.ASK_USER.value:
                        self.task_engine.set_state(task_id, TaskState.WAITING_FOR_APPROVAL)
                        task_data["current_step"] = step_idx
                        return {
                            "success": False,
                            "task_id": task_id,
                            "status": TaskState.WAITING_FOR_APPROVAL.value,
                            "approval_required": True,
                            "prompt": tool_output.get("prompt") or f"Permission required for '{step.objective}'.",
                            "step": step.model_dump(),
                            "tool_name": step.tool,
                            "action": step.input_data.get("operation") or step.objective
                        }

                # Observe & Verify
                self.task_engine.set_state(task_id, TaskState.OBSERVING)
                self.task_engine.set_state(task_id, TaskState.VERIFYING)
                verif = self.verification_engine.verify_step(tool_output, step.verification_condition)
                if verif.get("verified", False):
                    step.status = "completed"
                    step.output_data = tool_output.get("data")
                    obs_msg = f"Step {step_idx + 1} ({step.objective}): Verified - {verif.get('reason')}"
                    observations.append(obs_msg)
                    if step_callback:
                        step_callback({"event": "step_completed", "task_id": task_id, "step": step.model_dump(), "verification": verif})
                else:
                    step.status = "failed"
                    self.task_engine.set_state(task_id, TaskState.FAILED)
                    return {"success": False, "task_id": task_id, "error": f"Step verification failed: {verif.get('reason')}"}

            # Task Completion
            final_report = f"Successfully completed: '{goal}'.\n" + "\n".join(observations)
            self.task_engine.repo.update_task(
                task_id,
                status=TaskState.COMPLETED.value,
                final_result=final_report,
                verification_status="verified",
                observations="\n".join(observations)
            )
            self.task_engine.set_state(task_id, TaskState.COMPLETED)
            completion_payload = {
                "event": "task_completed",
                "task_id": task_id,
                "result": final_report,
                "intent_type": intent.intent_type,
                "target": intent.target,
                "parameters": intent.parameters
            }
            if step_callback:
                step_callback(completion_payload)

            return {
                "success": True,
                "task_id": task_id,
                "status": TaskState.COMPLETED.value,
                "final_result": final_report,
                "observations": observations,
                "intent_type": intent.intent_type,
                "target": intent.target,
                "parameters": intent.parameters
            }
        except Exception as ex:
            logger.exception(f"Error resuming task {task_id} after approval")
            self.task_engine.set_state(task_id, TaskState.FAILED, reason=str(ex))
            return {"success": False, "task_id": task_id, "status": TaskState.FAILED.value, "error": str(ex)}
