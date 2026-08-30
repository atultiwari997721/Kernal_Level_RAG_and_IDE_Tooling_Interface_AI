"""Tests for Full Architecture Shopping Website Scaffolding and Verification."""
import os
import shutil
from fastapi.testclient import TestClient
from apps.desktop.server import app
from core.goal_engine.engine import GoalEngine
from core.planner.planner import Planner


def test_goal_engine_understands_shopping_website_intent():
    engine = GoalEngine()
    intent = engine.understand_goal("create a shopping website at K:\\test_shop")
    assert intent.intent_type == "create_shopping_website"
    assert "test_shop" in intent.target


def test_planner_creates_shopping_website_pipeline():
    engine = GoalEngine()
    intent = engine.understand_goal("build an e-commerce store at K:\\test_store")
    plan = Planner.create_plan("task-shop-1", intent)

    assert len(plan.steps) == 9
    step_objectives = [s.objective for s in plan.steps]
    assert any("ARCHITECTURE.md" in o for o in step_objectives)
    assert any("index.html" in o for o in step_objectives)
    assert any("styles.css" in o for o in step_objectives)
    assert any("app.js" in o for o in step_objectives)
    assert any("server.py" in o for o in step_objectives)
    assert any("package.json" in o for o in step_objectives)
    assert any("run_shopping_website.bat" in o for o in step_objectives)


def test_end_to_end_autonomous_shopping_website_scaffolding():
    test_dir = os.path.join(os.getcwd(), "scratch_test_shopping_site")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    client = TestClient(app)
    try:
        res = client.post(
            "/api/kritimode/execute",
            json={
                "goal": f"create a shopping website at {test_dir}",
                "power_mode": "autonomous"
            }
        )
        assert res.status_code == 200
        data = res.json()

        assert data["success"] is True
        assert data["status"] == "completed"

        # Verify real physical files exist on disk with real content
        assert os.path.isdir(test_dir)
        arch_file = os.path.join(test_dir, "ARCHITECTURE.md")
        html_file = os.path.join(test_dir, "index.html")
        css_file = os.path.join(test_dir, "styles.css")
        js_file = os.path.join(test_dir, "app.js")
        py_file = os.path.join(test_dir, "server.py")
        pkg_file = os.path.join(test_dir, "package.json")
        bat_file = os.path.join(test_dir, "run_shopping_website.bat")

        assert os.path.isfile(arch_file) and os.path.getsize(arch_file) > 200
        assert os.path.isfile(html_file) and os.path.getsize(html_file) > 500
        assert os.path.isfile(css_file) and os.path.getsize(css_file) > 300
        assert os.path.isfile(js_file) and os.path.getsize(js_file) > 400
        assert os.path.isfile(py_file) and os.path.getsize(py_file) > 200
        assert os.path.isfile(pkg_file) and os.path.getsize(pkg_file) > 50
        assert os.path.isfile(bat_file)

    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
