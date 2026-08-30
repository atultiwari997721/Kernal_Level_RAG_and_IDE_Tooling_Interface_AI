"""Tests for Dynamic LLM Planning, Directory Actions, and Verifiable Execution."""
import os
from fastapi.testclient import TestClient
from apps.desktop.server import app, orchestrator
from core.goal_engine.engine import GoalEngine, GoalIntent
from core.planner.planner import Planner


def test_goal_engine_directory_and_file_intents():
    engine = GoalEngine(default_workdir=os.getcwd())

    # 1. Directory Listing
    intent = engine.understand_goal("list all files in this directory")
    assert intent.intent_type == "list_directory"
    assert "list_dir" in intent.parameters.get("operation", "")

    # 2. Folder creation
    intent = engine.understand_goal("mkdir K:\\TestNewFolder")
    assert intent.intent_type == "create_folder"
    assert "TestNewFolder" in intent.target

    # 3. Read file
    intent = engine.understand_goal("read file pyproject.toml")
    assert intent.intent_type == "read_file"
    assert "pyproject.toml" in intent.target

    # 4. Open-ended goal
    intent = engine.understand_goal("Deploy a microservice to Kubernetes cluster")
    assert intent.intent_type == "dynamic_llm_goal"


def test_planner_creates_real_directory_steps():
    engine = GoalEngine(default_workdir=os.getcwd())
    intent = engine.understand_goal("list files in current directory")

    plan = Planner.create_plan("test-task-dir", intent)
    assert len(plan.steps) == 1
    assert plan.steps[0].tool == "filesystem"
    assert plan.steps[0].input_data["operation"] == "list_dir"


def test_autonomous_directory_listing_execution():
    client = TestClient(app)
    res = client.post(
        "/api/kritimode/execute",
        json={
            "goal": "list files in this directory",
            "power_mode": "autonomous"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert data["status"] == "completed"
    assert "Successfully completed" in data["final_result"]
    assert len(data.get("observations", [])) > 0


def test_autonomous_file_read_execution():
    client = TestClient(app)
    res = client.post(
        "/api/kritimode/execute",
        json={
            "goal": "read file pyproject.toml",
            "power_mode": "autonomous"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert data["status"] == "completed"
