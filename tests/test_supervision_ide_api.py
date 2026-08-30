"""Tests for KritiSuperVision IDE API endpoints."""
import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from apps.desktop.server import app

client = TestClient(app)


@pytest.fixture
def temp_project():
    d = tempfile.mkdtemp(prefix="kriti_ide_test_")
    # Create sample files
    main_py = os.path.join(d, "main.py")
    with open(main_py, "w", encoding="utf-8") as f:
        f.write("def calculate_total(a, b):\n    return a + b\n\nclass InvoiceManager:\n    pass\n")

    readme = os.path.join(d, "README.md")
    with open(readme, "w", encoding="utf-8") as f:
        f.write("# Sample Project\n")

    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_ide_inspect_endpoint(temp_project):
    res = client.post("/api/supervision/inspect", json={"path": temp_project})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["file_count"] >= 2
    assert "main.py" in data["key_files"] or any(f["rel_path"] == "main.py" for f in data["file_tree"])
    assert len(data["symbols"]) >= 2
    assert any(s["name"] == "calculate_total" for s in data["symbols"])
    assert any(s["name"] == "InvoiceManager" for s in data["symbols"])


def test_ide_file_read_write(temp_project):
    # Read file
    res = client.get(f"/api/supervision/file?path={temp_project}&file=main.py")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "calculate_total" in data["content"]

    # Write file
    new_code = "def calculate_total(a, b):\n    return (a + b) * 2\n"
    write_res = client.post("/api/supervision/file", json={"path": temp_project, "file": "main.py", "content": new_code})
    assert write_res.status_code == 200
    w_data = write_res.json()
    assert w_data["success"] is True
    assert w_data["action"] == "modified"
    assert w_data["diff"] != ""

    # Verify content changed on disk
    verify_res = client.get(f"/api/supervision/file?path={temp_project}&file=main.py")
    assert "* 2" in verify_res.json()["content"]


def test_ide_save_plan(temp_project):
    plan_content = "# Implementation Plan\n\n## Goal\nTest Plan\n\n## Execution Steps\n1. Step 1\n"
    res = client.post("/api/supervision/plan/save", json={"path": temp_project, "markdown": plan_content})
    assert res.status_code == 200
    assert res.json()["success"] is True

    plan_on_disk = os.path.join(temp_project, "IMPLEMENTATION_PLAN.md")
    assert os.path.exists(plan_on_disk)
    with open(plan_on_disk, "r", encoding="utf-8") as f:
        assert "Test Plan" in f.read()


def test_terminal_run_endpoint(temp_project):
    res = client.post("/api/terminal/run", json={"path": temp_project, "command": "Write-Output 'KritiAI Terminal Active'"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "KritiAI Terminal Active" in data["stdout"]
    assert data["exit_code"] == 0
