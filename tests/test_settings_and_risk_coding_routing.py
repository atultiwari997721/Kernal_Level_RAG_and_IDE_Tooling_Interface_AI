"""Tests for Open Path Explorer Dispatch, Settings Model Dropdowns, and Risk-Mode Coding Escalation."""
import os
import tempfile
from fastapi.testclient import TestClient
from apps.desktop.server import app, model_router
from config.settings import PowerMode


def test_open_path_endpoint_directory_and_file():
    client = TestClient(app)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test directory
        res = client.post("/api/open-path", json={"path": tmpdir})
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Test file inside directory
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("hello")
        res_file = client.post("/api/open-path", json={"path": test_file})
        assert res_file.status_code == 200
        assert res_file.json()["success"] is True

        # Test file:/// URI scheme
        file_uri = f"file:///{test_file.replace(os.sep, '/')}"
        res_uri = client.post("/api/open-path", json={"path": file_uri})
        assert res_uri.status_code == 200
        assert res_uri.json()["success"] is True

        # Test non-existent child inside valid parent folder (should resolve parent)
        non_existent = os.path.join(tmpdir, "subfolder_not_yet_created")
        res_parent = client.post("/api/open-path", json={"path": non_existent})
        assert res_parent.status_code == 200
        assert res_parent.json()["success"] is True


def test_risk_mode_coding_escalation():
    # In autonomous or safe mode, coding task uses standard routing
    prov_safe, model_safe = model_router.route(task_type="coding", power_mode="safe")
    prov_auto, model_auto = model_router.route(task_type="coding", power_mode="autonomous")

    # In RISK mode only, coding task dynamically escalates to best coding model
    prov_risk, model_risk = model_router.route(task_type="coding", power_mode="risk")

    assert "coder" in model_risk.lower() or "code" in model_risk.lower() or "qwen" in model_risk.lower()
    # General task in risk mode does NOT escalate to coding model
    prov_gen, model_gen = model_router.route(task_type="general", power_mode="risk")
    assert "coder" not in (model_gen or "").lower()


def test_settings_api_model_selection_persistence():
    client = TestClient(app)
    payload = {
        "general_model": "ollama:qwen2.5:7b",
        "coding_model": "ollama:qwen2.5-coder:7b",
        "power_mode": "risk"
    }
    res = client.post("/api/config", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"

    cfg_res = client.get("/api/config")
    assert cfg_res.status_code == 200
    cfg = cfg_res.json()
    assert cfg["models"]["general_model"] == "ollama:qwen2.5:7b"
    assert cfg["models"]["coding_model"] == "ollama:qwen2.5-coder:7b"
    assert cfg["power_mode"] == "risk"

    # Reset back to auto
    client.post("/api/config", json={"general_model": "auto", "coding_model": "auto", "power_mode": "autonomous"})
