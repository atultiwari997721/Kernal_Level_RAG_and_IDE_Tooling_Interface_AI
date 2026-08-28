"""Tests for Extended Goal Engine (YouTube, Location-Aware Calculator, Web Search)."""
import os
from core.goal_engine.engine import GoalEngine


def test_understand_play_youtube_intent():
    ge = GoalEngine()

    intent1 = ge.understand_goal("Play Sita Ram song")
    assert intent1.intent_type == "play_youtube"
    assert "Sita Ram" in intent1.parameters["query"]

    intent2 = ge.understand_goal("Open YouTube and play Raske Kamar")
    assert intent2.intent_type == "play_youtube"
    assert "Raske Kamar" in intent2.parameters["query"]


def test_understand_create_calculator_specific_location():
    ge = GoalEngine(default_workdir="C:/Work")

    # Windows drive path
    intent1 = ge.understand_goal("Create a calculator in K:\\Projects\\Calc")
    assert intent1.intent_type == "create_calculator"
    assert os.path.normpath(intent1.parameters["path"]) == os.path.normpath("K:\\Projects\\Calc")

    # Desktop keyword
    intent2 = ge.understand_goal("Make a calculator app on Desktop")
    assert intent2.intent_type == "create_calculator"
    assert "Desktop" in intent2.parameters["path"]
    assert "Calculator" in intent2.parameters["path"]


def test_understand_search_web():
    ge = GoalEngine()
    intent = ge.understand_goal("Search web for Python FastAPI tutorial")
    assert intent.intent_type == "search_web"
    assert "FastAPI" in intent.parameters["query"]
