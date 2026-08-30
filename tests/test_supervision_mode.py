"""Tests for KritiSupervision Mode (Senior Developer Inspection, Modification, and Debugging)."""
import os
import shutil
import tempfile
from fastapi.testclient import TestClient
from apps.desktop.server import app


def test_supervision_inspect_discovers_project_architecture():
    client = TestClient(app)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample project in tmpdir
        with open(os.path.join(tmpdir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><head><title>Test App</title></head><body><nav>Nav</nav></body></html>")
        with open(os.path.join(tmpdir, "styles.css"), "w", encoding="utf-8") as f:
            f.write("body { background: #000; color: #fff; }")
        with open(os.path.join(tmpdir, "app.js"), "w", encoding="utf-8") as f:
            f.write("console.log('App running');")

        res = client.post("/api/supervision/inspect", json={"path": tmpdir})
        assert res.status_code == 200
        data = res.json()

        assert data["success"] is True
        assert data["file_count"] == 3
        assert "HTML5" in data["tech_stack"]
        assert "JavaScript" in data["tech_stack"]
        assert len(data["file_tree"]) == 3
        assert "index.html" in data["key_files"]


def test_supervision_modify_applies_senior_developer_refactor():
    client = TestClient(app)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create base app
        html_path = os.path.join(tmpdir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><head><title>Test App</title></head><body><nav><div class='logo'>Test</div></nav></body></html>")
        with open(os.path.join(tmpdir, "styles.css"), "w", encoding="utf-8") as f:
            f.write("body { background: #000; }")
        with open(os.path.join(tmpdir, "app.js"), "w", encoding="utf-8") as f:
            f.write("console.log('init');")

        # Request senior developer modification: Add dark mode toggle
        res = client.post(
            "/api/supervision/modify",
            json={
                "path": tmpdir,
                "instruction": "Add dark mode toggle button to the header and write styles"
            }
        )
        assert res.status_code == 200
        data = res.json()

        assert data["success"] is True
        assert len(data["files_modified"]) >= 2
        assert "themeToggle" in data["diff_summary"] or "Dark Mode" in data["diff_summary"] or "styles.css" in data["diff_summary"]

        # Verify physical file on disk was modified with verified content
        with open(html_path, "r", encoding="utf-8") as f:
            updated_html = f.read()
        assert "themeToggle" in updated_html or "Dark Mode" in updated_html
