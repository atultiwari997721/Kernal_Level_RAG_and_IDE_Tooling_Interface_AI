"""Comprehensive Unit Tests for KritiSuperVision ChangeManager Subsystem."""
import os
import shutil
import pytest
from pathlib import Path
from core.supervision.change_manager import (
    ChangeManager, ChangeRecord, ChangeGroup, get_change_manager, compute_sha256
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Setup a temporary project workspace with sample files."""
    proj = tmp_path / "sample_project"
    proj.mkdir()
    (proj / "index.html").write_text("<html><body><h1>Welcome</h1></body></html>", encoding="utf-8")
    (proj / "styles.css").write_text("body { margin: 0; background: #fff; }", encoding="utf-8")
    (proj / "app.js").write_text("console.log('init');", encoding="utf-8")
    return proj


def test_atomic_change_recording_and_undo_redo(temp_project: Path):
    cm = ChangeManager(str(temp_project))

    # User modifies styles.css
    res = cm.record_change(
        rel_path="styles.css",
        after_content="body { margin: 0; background: #111; color: #fff; }",
        author="user",
        operation="modify",
        reason="Updated dark background"
    )

    assert res["success"] is True
    assert res["author"] == "user"
    assert "background: #111" in (temp_project / "styles.css").read_text(encoding="utf-8")
    assert cm.undo_redo.can_undo() is True

    # Undo
    undo_res = cm.undo()
    assert undo_res["success"] is True
    assert undo_res["type"] == "atomic"
    assert "styles.css" in undo_res["reverted_files"]
    assert "background: #fff" in (temp_project / "styles.css").read_text(encoding="utf-8")
    assert cm.undo_redo.can_redo() is True

    # Redo
    redo_res = cm.redo()
    assert redo_res["success"] is True
    assert "styles.css" in redo_res["restored_files"]
    assert "background: #111" in (temp_project / "styles.css").read_text(encoding="utf-8")


def test_grouped_ai_change_and_multi_file_undo(temp_project: Path):
    cm = ChangeManager(str(temp_project))

    group = cm.start_change_group(
        title="Implement Dark Mode",
        author="kritiai",
        why="User requested dark theme toggle",
        what="Modified index.html, styles.css and created theme.js",
        risk_level="MEDIUM"
    )

    # 1. Modify index.html
    cm.record_change(
        rel_path="index.html",
        after_content="<html><body><h1>Welcome</h1><button id='dark'>Dark</button></body></html>",
        author="kritiai",
        group=group
    )

    # 2. Modify styles.css
    cm.record_change(
        rel_path="styles.css",
        after_content="body { background: #000; color: #fff; }",
        author="kritiai",
        group=group
    )

    # 3. Create theme.js
    cm.record_change(
        rel_path="theme.js",
        after_content="function toggle() { document.body.classList.toggle('dark'); }",
        author="kritiai",
        operation="create",
        group=group
    )

    cm.commit_change_group(group)

    assert (temp_project / "theme.js").exists()
    assert "button id='dark'" in (temp_project / "index.html").read_text(encoding="utf-8")

    # Undo entire AI Task
    undo_res = cm.undo()
    assert undo_res["success"] is True
    assert undo_res["type"] == "group"
    assert undo_res["title"] == "Implement Dark Mode"
    assert set(undo_res["reverted_files"]) == {"index.html", "styles.css", "theme.js"}

    # Verify physical file state reverted
    assert not (temp_project / "theme.js").exists()
    assert "button id='dark'" not in (temp_project / "index.html").read_text(encoding="utf-8")
    assert "background: #fff" in (temp_project / "styles.css").read_text(encoding="utf-8")

    # Redo entire AI Task
    redo_res = cm.redo()
    assert redo_res["success"] is True
    assert (temp_project / "theme.js").exists()
    assert "button id='dark'" in (temp_project / "index.html").read_text(encoding="utf-8")


def test_snapshots_create_and_restore(temp_project: Path):
    cm = ChangeManager(str(temp_project))

    # Create Snapshot before destructive edit
    snap = cm.snapshots.create_snapshot(str(temp_project), "Baseline Snapshot")
    assert snap["file_count"] >= 3
    snap_id = snap["snapshot_id"]

    # Delete index.html and corrupt styles.css
    (temp_project / "index.html").unlink()
    (temp_project / "styles.css").write_text("CORRUPTED", encoding="utf-8")

    assert not (temp_project / "index.html").exists()

    # Restore snapshot
    restore_res = cm.snapshots.restore_snapshot(str(temp_project), snap_id)
    assert restore_res["success"] is True
    assert (temp_project / "index.html").exists()
    assert "Welcome" in (temp_project / "index.html").read_text(encoding="utf-8")
    assert "background: #fff" in (temp_project / "styles.css").read_text(encoding="utf-8")


def test_conflict_detection(temp_project: Path):
    cm = ChangeManager(str(temp_project))
    initial_content = (temp_project / "index.html").read_text(encoding="utf-8")
    expected_hash = compute_sha256(initial_content)

    # User modifies file externally
    (temp_project / "index.html").write_text("<html><body>User Direct Edit</body></html>", encoding="utf-8")

    # AI tries to write assuming previous hash
    res = cm.record_change(
        rel_path="index.html",
        after_content="<html><body>AI Overwrite</body></html>",
        author="kritiai",
        expected_base_hash=expected_hash
    )

    assert res["success"] is False
    assert res["conflict"] is True
    assert "modified since last analysis" in res["error"]

    # Confirm user's edit was preserved
    assert "User Direct Edit" in (temp_project / "index.html").read_text(encoding="utf-8")


def test_terminal_filesystem_change_tracking(temp_project: Path):
    cm = ChangeManager(str(temp_project))
    before_manifest = cm.snapshot_filesystem_state()

    # Simulate terminal command (e.g. npm init or touch new_build.log)
    (temp_project / "build.log").write_text("Build succeeded at 14:30", encoding="utf-8")

    changes = cm.track_terminal_changes(before_manifest, "npm run build")
    assert len(changes) == 1
    assert changes[0].author == "terminal"
    assert changes[0].file_path == "build.log"
    assert changes[0].operation == "create"

    # Verify history recorded terminal operation
    timeline = cm.get_timeline()
    assert any(t["author"] == "terminal" and "build.log" in t["files"] for t in timeline)
