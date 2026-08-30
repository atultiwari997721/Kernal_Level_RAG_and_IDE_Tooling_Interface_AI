"""Integration Tests for KritiSuperVision Collaborative Editing, Undo/Redo, and History REST Endpoints."""
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from apps.desktop.server import app


@pytest.fixture
def test_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "collab_workspace"
    ws.mkdir()
    (ws / "index.html").write_text("<!DOCTYPE html><html><body><h1>Title</h1></body></html>", encoding="utf-8")
    (ws / "styles.css").write_text("body { color: blue; }", encoding="utf-8")
    (ws / "data.json").write_text('{"count": 42, "enabled": true}', encoding="utf-8")
    return ws


def test_file_create_rename_delete_endpoints(test_workspace: Path):
    client = TestClient(app)
    ws_str = str(test_workspace)

    # 1. Create file
    res = client.post("/api/supervision/file/create", json={
        "path": ws_str,
        "file": "components/Header.jsx",
        "content": "export function Header() { return <header />; }"
    })
    assert res.status_code == 200
    assert (test_workspace / "components" / "Header.jsx").exists()

    # 2. Rename file
    res = client.post("/api/supervision/file/rename", json={
        "path": ws_str,
        "old_path": "components/Header.jsx",
        "new_path": "components/Navbar.jsx"
    })
    assert res.status_code == 200
    assert not (test_workspace / "components" / "Header.jsx").exists()
    assert (test_workspace / "components" / "Navbar.jsx").exists()

    # 3. Delete file
    res = client.post("/api/supervision/file/delete", json={
        "path": ws_str,
        "file": "components/Navbar.jsx"
    })
    assert res.status_code == 200
    assert not (test_workspace / "components" / "Navbar.jsx").exists()


def test_folder_create_delete_endpoints(test_workspace: Path):
    client = TestClient(app)
    ws_str = str(test_workspace)

    # Create folder
    res = client.post("/api/supervision/folder/create", json={
        "path": ws_str,
        "folder": "src/utils"
    })
    assert res.status_code == 200
    assert (test_workspace / "src" / "utils").is_dir()

    # Delete folder
    res = client.post("/api/supervision/folder/delete", json={
        "path": ws_str,
        "folder": "src/utils"
    })
    assert res.status_code == 200
    assert not (test_workspace / "src" / "utils").exists()


def test_undo_and_redo_endpoints(test_workspace: Path):
    client = TestClient(app)
    ws_str = str(test_workspace)

    # Write file modification
    res = client.post("/api/supervision/file", json={
        "path": ws_str,
        "file": "styles.css",
        "content": "body { color: red; font-size: 16px; }",
        "author": "user",
        "reason": "Changed font size"
    })
    assert res.status_code == 200
    assert "color: red" in (test_workspace / "styles.css").read_text(encoding="utf-8")

    # Undo
    undo_res = client.post("/api/supervision/undo", json={"path": ws_str})
    assert undo_res.status_code == 200
    assert undo_res.json()["success"] is True
    assert "color: blue" in (test_workspace / "styles.css").read_text(encoding="utf-8")

    # Redo
    redo_res = client.post("/api/supervision/redo", json={"path": ws_str})
    assert redo_res.status_code == 200
    assert redo_res.json()["success"] is True
    assert "color: red" in (test_workspace / "styles.css").read_text(encoding="utf-8")


def test_history_and_snapshots_endpoints(test_workspace: Path):
    client = TestClient(app)
    ws_str = str(test_workspace)

    # Create Snapshot
    snap_res = client.post("/api/supervision/snapshots", json={
        "path": ws_str,
        "title": "Pre-Release Snapshot"
    })
    assert snap_res.status_code == 200
    snap_id = snap_res.json()["snapshot_id"]

    # List Snapshots
    list_res = client.get(f"/api/supervision/snapshots?path={ws_str}")
    assert list_res.status_code == 200
    snapshots = list_res.json()
    assert any(s["snapshot_id"] == snap_id for s in snapshots)

    # Check History timeline
    hist_res = client.get(f"/api/supervision/history?path={ws_str}")
    assert hist_res.status_code == 200
    assert isinstance(hist_res.json(), list)

    # Corrupt a file and restore
    (test_workspace / "styles.css").write_text("CORRUPTED", encoding="utf-8")
    restore_res = client.post("/api/supervision/snapshots/restore", json={
        "path": ws_str,
        "snapshot_id": snap_id
    })
    assert restore_res.status_code == 200
    assert "color: blue" in (test_workspace / "styles.css").read_text(encoding="utf-8")


def test_code_format_endpoint(test_workspace: Path):
    client = TestClient(app)
    ws_str = str(test_workspace)

    # Write unformatted JSON
    (test_workspace / "unformatted.json").write_text('{"a":1,"b":[2,3]}', encoding="utf-8")

    res = client.post("/api/supervision/format", json={
        "path": ws_str,
        "file": "unformatted.json"
    })
    assert res.status_code == 200
    assert res.json()["formatted"] is True
    formatted_content = (test_workspace / "unformatted.json").read_text(encoding="utf-8")
    assert "\n" in formatted_content
    assert '  "a": 1' in formatted_content


def test_ai_changes_decide_endpoint(test_workspace: Path):
    client = TestClient(app)
    ws_str = str(test_workspace)
    initial_text = (test_workspace / "index.html").read_text(encoding="utf-8")

    # Apply a senior developer change
    modify_res = client.post("/api/supervision/modify", json={
        "path": ws_str,
        "instruction": "Add dark mode toggle"
    })
    assert modify_res.status_code == 200
    mod_data = modify_res.json()
    group_id = mod_data.get("group_id")
    assert group_id is not None
    modified_text = (test_workspace / "index.html").read_text(encoding="utf-8")
    assert modified_text != initial_text

    # Reject and undo task
    decide_res = client.post("/api/supervision/changes/decide", json={
        "path": ws_str,
        "group_id": group_id,
        "decision": "reject"
    })
    assert decide_res.status_code == 200
    assert decide_res.json()["success"] is True
    # Reverted back to exact initial content
    reverted_text = (test_workspace / "index.html").read_text(encoding="utf-8")
    assert reverted_text == initial_text


def test_filesystem_browse_and_drives_endpoints(test_workspace: Path):
    client = TestClient(app)
    ws_str = str(test_workspace)

    # 1. Drives
    drives_res = client.get("/api/fs/drives")
    assert drives_res.status_code == 200
    drives = drives_res.json()
    assert isinstance(drives, list)
    assert len(drives) >= 1

    # 2. Browse directory
    browse_res = client.get(f"/api/fs/browse?path={ws_str}")
    assert browse_res.status_code == 200
    data = browse_res.json()
    assert data["success"] is True
    assert data["current_path"] == str(test_workspace)
    assert any(f["name"] == "index.html" for f in data["files"])
    assert any(f["name"] == "styles.css" for f in data["files"])


def test_supervision_command_execution(test_workspace: Path):
    client = TestClient(app)
    ws_str = str(test_workspace)

    # Execute a command through supervision modify
    cmd_res = client.post("/api/supervision/modify", json={
        "path": ws_str,
        "instruction": "run python -c \"print('SUPERVISION_EXEC_OK')\""
    })
    assert cmd_res.status_code == 200
    data = cmd_res.json()
    assert data["success"] is True
    assert data.get("is_command") is True
    assert "SUPERVISION_EXEC_OK" in data.get("stdout", "")
    assert data.get("exit_code") == 0
