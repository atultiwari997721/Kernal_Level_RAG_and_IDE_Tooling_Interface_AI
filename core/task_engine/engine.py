"""Task Execution Lifecycle Engine for KritiAI."""
import json
import logging
from typing import Any, Dict, List, Optional
from database.repository import Repository
from core.state_machine.states import TaskState, TaskStateMachine
from core.planner.planner import ExecutionPlan, PlanStep
from security.sandbox.watchdog import get_emergency_stop_manager

logger = logging.getLogger("kritiai.task_engine")


class TaskEngine:
    """Manages the persistent lifecycle, steps, and state transitions of a Task."""

    def __init__(self, repo: Optional[Repository] = None):
        self.repo = repo or Repository()

    def create_task(
        self,
        goal: str,
        session_id: Optional[str] = None,
        mode: str = "kritimode",
        power_mode: str = "autonomous"
    ) -> Dict[str, Any]:
        task = self.repo.create_task(
            goal=goal,
            session_id=session_id,
            mode=mode,
            power_mode=power_mode
        )
        get_emergency_stop_manager().register_task(task["id"])
        return task

    def set_state(self, task_id: str, new_state: TaskState, reason: Optional[str] = None) -> Dict[str, Any]:
        task = self.repo.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        current_state = TaskState(task["status"])
        TaskStateMachine.validate_transition(current_state, new_state)

        logger.info(f"[TASK {task_id}] State transition: {current_state.value} -> {new_state.value} ({reason or ''})")
        updated = self.repo.update_task(task_id, status=new_state.value)

        if new_state in (TaskState.COMPLETED, TaskState.CANCELLED, TaskState.FAILED):
            get_emergency_stop_manager().unregister_task(task_id)

        return updated

    def attach_plan(self, task_id: str, plan: ExecutionPlan) -> Dict[str, Any]:
        steps_dict = [s.model_dump() for s in plan.steps]
        self.repo.save_task_steps(task_id, steps_dict)
        return self.repo.update_task(task_id, plan=steps_dict)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_task(task_id)

    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.repo.list_tasks(limit=limit)

    def pause_task(self, task_id: str) -> Dict[str, Any]:
        return self.set_state(task_id, TaskState.PAUSED, reason="User requested pause")

    def resume_task(self, task_id: str) -> Dict[str, Any]:
        return self.set_state(task_id, TaskState.EXECUTING, reason="User resumed task")

    def cancel_task(self, task_id: str, reason: str = "User cancelled task") -> Dict[str, Any]:
        return self.set_state(task_id, TaskState.CANCELLED, reason=reason)
