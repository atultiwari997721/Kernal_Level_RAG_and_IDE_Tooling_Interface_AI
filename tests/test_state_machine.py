"""Tests for KritiAI Task State Machine."""
import pytest
from core.state_machine.states import TaskState, TaskStateMachine


def test_valid_state_transitions():
    assert TaskStateMachine.can_transition(TaskState.CREATED, TaskState.UNDERSTANDING)
    assert TaskStateMachine.can_transition(TaskState.UNDERSTANDING, TaskState.PLANNING)
    assert TaskStateMachine.can_transition(TaskState.PLANNING, TaskState.EXECUTING)
    assert TaskStateMachine.can_transition(TaskState.EXECUTING, TaskState.OBSERVING)
    assert TaskStateMachine.can_transition(TaskState.OBSERVING, TaskState.VERIFYING)
    assert TaskStateMachine.can_transition(TaskState.VERIFYING, TaskState.COMPLETED)


def test_invalid_state_transitions():
    assert not TaskStateMachine.can_transition(TaskState.CREATED, TaskState.COMPLETED)
    assert not TaskStateMachine.can_transition(TaskState.COMPLETED, TaskState.EXECUTING)
    assert not TaskStateMachine.can_transition(TaskState.CANCELLED, TaskState.PLANNING)

    with pytest.raises(ValueError):
        TaskStateMachine.validate_transition(TaskState.CREATED, TaskState.COMPLETED)


def test_same_state_is_noop():
    assert TaskStateMachine.can_transition(TaskState.EXECUTING, TaskState.EXECUTING)
