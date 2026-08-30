"""Tests for Autonomous Adaptive Execution Engine on Novel, Unseen Goals."""
import os
import shutil
from fastapi.testclient import TestClient
from apps.desktop.server import app
from core.goal_engine.engine import GoalEngine
from core.planner.planner import Planner
from core.planner.code_synthesizer import detect_runtime, synthesize_project_artifacts


def test_detect_runtime_and_code_synthesizer():
    assert detect_runtime("Build a retro arcade game in HTML5") == "web"
    assert detect_runtime("Write a python script to benchmark disk speeds") == "python"
    assert detect_runtime("Create a powershell script to monitor services") == "powershell"

    artifacts, cmd = synthesize_project_artifacts("Build a retro arcade game in HTML5", "K:\\test")
    assert "index.html" in artifacts
    assert "styles.css" in artifacts
    assert "app.js" in artifacts
    assert "run.bat" in artifacts

    py_artifacts, py_cmd = synthesize_project_artifacts("Create a python disk speed benchmark", "K:\\test")
    assert "main.py" in py_artifacts
    assert "run.bat" in py_artifacts
    assert "python" in py_cmd


def test_planner_creates_adaptive_plan_for_novel_goal():
    engine = GoalEngine()
    # Web game goal
    intent_web = engine.understand_goal("Build a Snake game in HTML5 at K:\\test_snake")
    plan_web = Planner.create_plan("task-adaptive-1", intent_web)
    assert len(plan_web.steps) >= 4
    step_tools_web = [s.tool for s in plan_web.steps]
    assert "filesystem" in step_tools_web
    assert "browser" in step_tools_web

    # Python utility goal
    intent_py = engine.understand_goal("Create a python disk speed benchmark in K:\\test_bench")
    plan_py = Planner.create_plan("task-adaptive-2", intent_py)
    assert len(plan_py.steps) >= 4
    step_tools_py = [s.tool for s in plan_py.steps]
    assert "filesystem" in step_tools_py
    assert "powershell" in step_tools_py


def test_end_to_end_novel_python_script_execution():
    test_dir = os.path.join(os.getcwd(), "scratch_test_adaptive_python")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    client = TestClient(app)
    try:
        res = client.post(
            "/api/kritimode/execute",
            json={
                "goal": f"Create a python disk speed benchmark in {test_dir}",
                "power_mode": "autonomous"
            }
        )
        assert res.status_code == 200
        data = res.json()

        assert data["success"] is True
        assert data["status"] == "completed"

        # Verify real physical files exist on disk with real content
        assert os.path.isdir(test_dir)
        py_file = os.path.join(test_dir, "main.py")
        bat_file = os.path.join(test_dir, "run.bat")
        readme_file = os.path.join(test_dir, "README.md")

        assert os.path.isfile(py_file) and os.path.getsize(py_file) > 100
        assert os.path.isfile(bat_file)
        assert os.path.isfile(readme_file)

        # Observations should show actual execution of the python script
        obs_text = " ".join(data.get("observations", []))
        assert "Benchmark" in obs_text or "exit code 0" in obs_text.lower() or "python" in obs_text.lower()

    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


def test_end_to_end_novel_web_game_scaffolding():
    test_dir = os.path.join(os.getcwd(), "scratch_test_adaptive_game")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    client = TestClient(app)
    try:
        res = client.post(
            "/api/kritimode/execute",
            json={
                "goal": f"Build a Snake retro game in HTML5 in {test_dir}",
                "power_mode": "autonomous"
            }
        )
        assert res.status_code == 200
        data = res.json()

        assert data["success"] is True
        assert data["status"] == "completed"

        # Verify HTML, CSS, JS, and Bat files exist
        assert os.path.isfile(os.path.join(test_dir, "index.html"))
        assert os.path.isfile(os.path.join(test_dir, "styles.css"))
        assert os.path.isfile(os.path.join(test_dir, "app.js"))
        assert os.path.isfile(os.path.join(test_dir, "run.bat"))

    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
