"""Task States and Deterministic State Machine for KritiAI."""
from enum import Enum
from typing import Dict, Set


class TaskState(str, Enum):
    """Task states as defined in Section 12."""
    CREATED = "created"
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    EXECUTING = "executing"
    OBSERVING = "observing"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    WAITING_FOR_USER = "waiting_for_user"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"


# Explicit valid transitions
VALID_TRANSITIONS: Dict[TaskState, Set[TaskState]] = {
    TaskState.CREATED: {TaskState.UNDERSTANDING, TaskState.CANCELLED},
    TaskState.UNDERSTANDING: {TaskState.PLANNING, TaskState.WAITING_FOR_USER, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.PLANNING: {TaskState.WAITING_FOR_APPROVAL, TaskState.EXECUTING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.WAITING_FOR_APPROVAL: {TaskState.EXECUTING, TaskState.CANCELLED, TaskState.WAITING_FOR_USER},
    TaskState.EXECUTING: {TaskState.OBSERVING, TaskState.PAUSED, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.OBSERVING: {TaskState.VERIFYING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.VERIFYING: {TaskState.EXECUTING, TaskState.RECOVERING, TaskState.COMPLETED, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.RECOVERING: {TaskState.EXECUTING, TaskState.PLANNING, TaskState.WAITING_FOR_USER, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.WAITING_FOR_USER: {TaskState.EXECUTING, TaskState.PLANNING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.PAUSED: {TaskState.EXECUTING, TaskState.CANCELLED},
    TaskState.CANCELLED: set(),
    TaskState.FAILED: {TaskState.RECOVERING, TaskState.CREATED},  # Can be restarted
    TaskState.COMPLETED: set()
}


class TaskStateMachine:
    """Validates and enforces deterministic task state transitions."""

    @staticmethod
    def can_transition(from_state: TaskState, to_state: TaskState) -> bool:
        if from_state == to_state:
            return True
        allowed = VALID_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @staticmethod
    def validate_transition(from_state: TaskState, to_state: TaskState) -> None:
        if not TaskStateMachine.can_transition(from_state, to_state):
            raise ValueError(f"Invalid task transition from {from_state.value} to {to_state.value}")
