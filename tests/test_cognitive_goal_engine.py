"""Tests for Cognitive Goal Engine and StructuredTask representation."""
import pytest
from core.goal_engine.engine import GoalEngine, StructuredTask, GoalIntent
from security.policies.models import RiskLevel


def test_structured_task_dataclass():
    task = StructuredTask(
        goal="Create an automated log cleaner",
        intent="code_generation",
        is_informational=False,
        requirements=["Delete logs older than 7 days", "Log deletions to console"],
        dependencies=["Python 3.x"],
        planned_actions=["Create script", "Execute tests"],
        required_tools=["filesystem", "terminal"]
    )
    assert task.goal == "Create an automated log cleaner"
    assert task.intent == "code_generation"
    assert task.is_informational is False
    assert len(task.requirements) == 2
    assert "filesystem" in task.required_tools


def test_informational_query_detection():
    engine = GoalEngine()
    queries = [
        "What is React and why do people use it?",
        "Explain the difference between SQL and NoSQL databases",
        "How does Docker networking work under the hood?",
        "Who created Python?"
    ]

    for q in queries:
        intent = engine.understand_goal(q)
        assert intent.is_informational is True
        assert intent.intent_type == "information_query"
        assert intent.structured_task is not None
        assert intent.structured_task.is_informational is True
        assert "model_gateway" in intent.structured_task.required_tools


def test_media_playback_zero_hardcoding():
    engine = GoalEngine()

    # Explicit song
    intent = engine.understand_goal("Play Bohemian Rhapsody on YouTube")
    assert intent.intent_type == "play_youtube"
    assert "Bohemian Rhapsody" in intent.target
    assert intent.target != "Sita Ram song"

    # Contextual query without hardcoding
    intent2 = engine.understand_goal("Play some music")
    assert intent2.intent_type == "play_youtube"
    assert intent2.target != "Sita Ram song"


def test_arbitrary_novel_project_understanding():
    engine = GoalEngine()
    intent = engine.understand_goal("Create a real-time crypto price tracker in K:\\CryptoApp")

    assert intent.intent_type == "dynamic_llm_goal"
    assert intent.is_informational is False
    assert "CryptoApp" in intent.target
    assert intent.structured_task is not None
    assert len(intent.structured_task.planned_actions) >= 2
    assert "filesystem" in intent.structured_task.required_tools
