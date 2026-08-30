"""ChangeManager Subsystem for KritiSuperVision.

Provides a complete User + AI Collaborative Editing, Change Tracking,
Global Multi-level Undo/Redo, Snapshots, Conflict Detection, and Change History.
Independent of LLMs — operates via deterministic file patches and state snapshots.
"""
import os
import shutil
import hashlib
import difflib
import json
import time
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple, Set

logger = logging.getLogger("kritiai.change_manager")

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".idea", ".vscode", "dist", "build", ".kriti_history"}


def compute_sha256(content: str) -> str:
    """Compute SHA-256 hash of a string content."""
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


def compute_file_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file on disk."""
    if not os.path.isfile(file_path):
        return ""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as fp:
            while chunk := fp.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


class ChangeRecord:
    """Structured record of an atomic file modification."""

    def __init__(
        self,
        change_id: Optional[str] = None,
        group_id: Optional[str] = None,
        author: str = "user",  # user | kritiai | terminal | formatter | tool
        timestamp: Optional[str] = None,
        operation: str = "modify",  # modify | create | delete | rename
        file_path: str = "",
        before_content: str = "",
        after_content: str = "",
        diff: str = "",
        reason: str = "",
        task_id: Optional[str] = None,
        risk_level: str = "LOW",
        verified: bool = True,
        before_hash: str = "",
        after_hash: str = ""
    ):
        self.change_id = change_id or f"chg_{uuid.uuid4().hex[:8]}"
        self.group_id = group_id
        self.author = author
        self.timestamp = timestamp or time.strftime("%Y-%m-%d %H:%M:%S")
        self.operation = operation
        self.file_path = file_path
        self.before_content = before_content
        self.after_content = after_content
        self.before_hash = before_hash or compute_sha256(before_content)
        self.after_hash = after_hash or compute_sha256(after_content)
        self.diff = diff or self._generate_diff()
        self.reason = reason
        self.task_id = task_id
        self.risk_level = risk_level
        self.verified = verified

    def _generate_diff(self) -> str:
        if self.before_content == self.after_content:
            return ""
        diff_lines = list(difflib.unified_diff(
            self.before_content.splitlines(keepends=True),
            self.after_content.splitlines(keepends=True),
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}"
        ))
        return "".join(diff_lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "group_id": self.group_id,
            "author": self.author,
            "timestamp": self.timestamp,
            "operation": self.operation,
            "file_path": self.file_path,
            "before_hash": self.before_hash,
            "after_hash": self.after_hash,
            "diff": self.diff,
            "reason": self.reason,
            "task_id": self.task_id,
            "risk_level": self.risk_level,
            "verified": self.verified,
            "before_content": self.before_content,
            "after_content": self.after_content
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChangeRecord":
        return cls(
            change_id=data.get("change_id"),
            group_id=data.get("group_id"),
            author=data.get("author", "user"),
            timestamp=data.get("timestamp"),
            operation=data.get("operation", "modify"),
            file_path=data.get("file_path", ""),
            before_content=data.get("before_content", ""),
            after_content=data.get("after_content", ""),
            diff=data.get("diff", ""),
            reason=data.get("reason", ""),
            task_id=data.get("task_id"),
            risk_level=data.get("risk_level", "LOW"),
            verified=data.get("verified", True),
            before_hash=data.get("before_hash", ""),
            after_hash=data.get("after_hash", "")
        )


class ChangeGroup:
    """Logical task grouping multiple atomic file changes together (e.g. AI task or refactor)."""

    def __init__(
        self,
        group_id: Optional[str] = None,
        title: str = "",
        author: str = "kritiai",
        timestamp: Optional[str] = None,
        task_id: Optional[str] = None,
        why: str = "",
        what: str = "",
        risk_level: str = "MEDIUM",
        status: str = "applied",  # applied | undone | rejected
        changes: Optional[List[ChangeRecord]] = None
    ):
        self.group_id = group_id or f"grp_{uuid.uuid4().hex[:8]}"
        self.title = title
        self.author = author
        self.timestamp = timestamp or time.strftime("%Y-%m-%d %H:%M:%S")
        self.task_id = task_id
        self.why = why
        self.what = what
        self.risk_level = risk_level
        self.status = status
        self.changes: List[ChangeRecord] = changes or []

    def add_change(self, change: ChangeRecord) -> None:
        change.group_id = self.group_id
        self.changes.append(change)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "title": self.title,
            "author": self.author,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "why": self.why,
            "what": self.what,
            "risk_level": self.risk_level,
            "status": self.status,
            "files": [c.file_path for c in self.changes],
            "changes": [c.to_dict() for c in self.changes]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChangeGroup":
        changes = [ChangeRecord.from_dict(c) for c in data.get("changes", [])]
        return cls(
            group_id=data.get("group_id"),
            title=data.get("title", ""),
            author=data.get("author", "kritiai"),
            timestamp=data.get("timestamp"),
            task_id=data.get("task_id"),
            why=data.get("why", ""),
            what=data.get("what", ""),
            risk_level=data.get("risk_level", "MEDIUM"),
            status=data.get("status", "applied"),
            changes=changes
        )


class SnapshotManager:
    """Creates, lists, and restores local filesystem snapshots."""

    def __init__(self, history_dir: str):
        self.snapshots_dir = os.path.join(history_dir, "snapshots")
        os.makedirs(self.snapshots_dir, exist_ok=True)

    def create_snapshot(self, project_dir: str, title: str) -> Dict[str, Any]:
        """Create a complete copy of the project files in the snapshot store."""
        snap_id = f"snap_{int(time.time())}_{uuid.uuid4().hex[:4]}"
        snap_path = os.path.join(self.snapshots_dir, snap_id)
        os.makedirs(snap_path, exist_ok=True)

        manifest: Dict[str, str] = {}
        file_count = 0

        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                full_f = os.path.join(root, f)
                rel_f = os.path.relpath(full_f, project_dir)
                dest_f = os.path.join(snap_path, rel_f)
                os.makedirs(os.path.dirname(dest_f), exist_ok=True)
                try:
                    shutil.copy2(full_f, dest_f)
                    manifest[rel_f] = compute_file_sha256(full_f)
                    file_count += 1
                except Exception as ex:
                    logger.warning(f"Could not copy file '{rel_f}' for snapshot: {ex}")

        metadata = {
            "snapshot_id": snap_id,
            "title": title,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "file_count": file_count,
            "manifest": manifest
        }

        with open(os.path.join(snap_path, "snapshot.json"), "w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2)

        return metadata

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots ordered chronologically newest first."""
        snapshots: List[Dict[str, Any]] = []
        if not os.path.isdir(self.snapshots_dir):
            return snapshots

        for d in os.listdir(self.snapshots_dir):
            meta_path = os.path.join(self.snapshots_dir, d, "snapshot.json")
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as fp:
                        snapshots.append(json.load(fp))
                except Exception:
                    pass

        snapshots.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
        return snapshots

    def restore_snapshot(self, project_dir: str, snapshot_id: str) -> Dict[str, Any]:
        """Restore all project files from a specific snapshot."""
        snap_path = os.path.join(self.snapshots_dir, snapshot_id)
        meta_path = os.path.join(snap_path, "snapshot.json")
        if not os.path.isfile(meta_path):
            return {"success": False, "error": f"Snapshot '{snapshot_id}' not found."}

        with open(meta_path, "r", encoding="utf-8") as fp:
            meta = json.load(fp)

        restored_files = []
        for rel_path in meta.get("manifest", {}):
            src_file = os.path.join(snap_path, rel_path)
            dest_file = os.path.join(project_dir, rel_path)
            if os.path.isfile(src_file):
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(src_file, dest_file)
                restored_files.append(rel_path)

        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "title": meta.get("title"),
            "restored_count": len(restored_files),
            "files": restored_files
        }


class ConflictManager:
    """Detects when a file has been modified concurrently by the user or external process."""

    @staticmethod
    def check_conflict(project_dir: str, rel_path: str, expected_base_hash: Optional[str]) -> Dict[str, Any]:
        """Verify whether current file on disk matches expected base hash."""
        if not expected_base_hash:
            return {"has_conflict": False}

        full_path = os.path.normpath(os.path.join(project_dir, rel_path))
        if not os.path.exists(full_path):
            if expected_base_hash != "":
                return {
                    "has_conflict": True,
                    "reason": "File was deleted externally",
                    "path": rel_path
                }
            return {"has_conflict": False}

        current_hash = compute_file_sha256(full_path)
        if current_hash != expected_base_hash:
            return {
                "has_conflict": True,
                "reason": "User or external changes detected. File has been modified since last analysis.",
                "path": rel_path,
                "expected_hash": expected_base_hash,
                "current_hash": current_hash
            }

        return {"has_conflict": False}


class HistoryStore:
    """Persists change history to disk in `.kriti_history/history.json`."""

    def __init__(self, history_dir: str):
        self.history_file = os.path.join(history_dir, "history.json")
        os.makedirs(history_dir, exist_ok=True)

    def load_history(self) -> Tuple[List[ChangeRecord], List[ChangeGroup]]:
        """Load atomic changes and groups from disk."""
        if not os.path.isfile(self.history_file):
            return [], []
        try:
            with open(self.history_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            records = [ChangeRecord.from_dict(r) for r in data.get("records", [])]
            groups = [ChangeGroup.from_dict(g) for g in data.get("groups", [])]
            return records, groups
        except Exception as e:
            logger.warning(f"Could not load change history: {e}")
            return [], []

    def save_history(self, records: List[ChangeRecord], groups: List[ChangeGroup]) -> None:
        """Persist changes and groups to disk."""
        try:
            data = {
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "records": [r.to_dict() for r in records[-500:]],  # keep last 500 records
                "groups": [g.to_dict() for g in groups[-100:]]     # keep last 100 groups
            }
            with open(self.history_file, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
        except Exception as e:
            logger.warning(f"Could not save change history: {e}")


class UndoRedoManager:
    """Global undo and redo stacks for atomic and grouped file changes."""

    def __init__(self):
        self.undo_stack: List[Dict[str, Any]] = []  # items are {"type": "atomic"|"group", "data": ChangeRecord|ChangeGroup}
        self.redo_stack: List[Dict[str, Any]] = []

    def push_change(self, change: ChangeRecord) -> None:
        self.undo_stack.append({"type": "atomic", "data": change})
        self.redo_stack.clear()

    def push_group(self, group: ChangeGroup) -> None:
        self.undo_stack.append({"type": "group", "data": group})
        self.redo_stack.clear()

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def peek_undo(self) -> Optional[Dict[str, Any]]:
        return self.undo_stack[-1] if self.undo_stack else None

    def peek_redo(self) -> Optional[Dict[str, Any]]:
        return self.redo_stack[-1] if self.redo_stack else None


class ChangeManager:
    """Complete User + AI Collaborative Change Management Facade for a Project Workspace."""

    def __init__(self, project_dir: str):
        self.project_dir = os.path.normpath(project_dir)
        self.history_dir = os.path.join(self.project_dir, ".kriti_history")
        self.snapshots = SnapshotManager(self.history_dir)
        self.history_store = HistoryStore(self.history_dir)
        self.conflict_mgr = ConflictManager()
        self.undo_redo = UndoRedoManager()

        # Load persisted history
        self.records: List[ChangeRecord] = []
        self.groups: List[ChangeGroup] = []
        loaded_records, loaded_groups = self.history_store.load_history()
        self.records.extend(loaded_records)
        self.groups.extend(loaded_groups)

        # Populate undo stack from loaded records
        for g in self.groups:
            if g.status == "applied":
                self.undo_redo.undo_stack.append({"type": "group", "data": g})

    # =========================================================================
    # RECORDING CHANGES
    # =========================================================================

    def record_change(
        self,
        rel_path: str,
        after_content: str,
        author: str = "user",
        operation: str = "modify",
        reason: str = "",
        task_id: Optional[str] = None,
        risk_level: str = "LOW",
        group: Optional[ChangeGroup] = None,
        expected_base_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """Apply a file change, verify conflicts, and log to change history."""
        full_path = os.path.normpath(os.path.join(self.project_dir, rel_path))

        # Check for concurrent conflicts
        conflict = self.conflict_mgr.check_conflict(self.project_dir, rel_path, expected_base_hash)
        if conflict.get("has_conflict"):
            return {
                "success": False,
                "conflict": True,
                "error": conflict.get("reason"),
                "path": rel_path
            }

        # Read before content
        before_content = ""
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as fp:
                    before_content = fp.read()
            except Exception:
                before_content = ""

        # Write new content to disk
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as fp:
            fp.write(after_content)

        change = ChangeRecord(
            group_id=group.group_id if group else None,
            author=author,
            operation=operation,
            file_path=rel_path,
            before_content=before_content,
            after_content=after_content,
            reason=reason or f"File {operation} by {author}",
            task_id=task_id,
            risk_level=risk_level
        )

        self.records.append(change)
        if group:
            group.add_change(change)
        else:
            self.undo_redo.push_change(change)

        self.history_store.save_history(self.records, self.groups)

        return {
            "success": True,
            "change_id": change.change_id,
            "path": rel_path,
            "author": author,
            "operation": operation,
            "diff": change.diff,
            "before_hash": change.before_hash,
            "after_hash": change.after_hash
        }

    def start_change_group(
        self,
        title: str,
        author: str = "kritiai",
        task_id: Optional[str] = None,
        why: str = "",
        what: str = "",
        risk_level: str = "MEDIUM"
    ) -> ChangeGroup:
        """Create a new logical change group for an AI task or refactor."""
        group = ChangeGroup(
            title=title,
            author=author,
            task_id=task_id,
            why=why,
            what=what,
            risk_level=risk_level
        )
        return group

    def commit_change_group(self, group: ChangeGroup) -> None:
        """Commit a completed multi-file change group to history and undo stack."""
        if not group.changes:
            return
        self.groups.append(group)
        self.undo_redo.push_group(group)
        self.history_store.save_history(self.records, self.groups)

    # =========================================================================
    # UNDO & REDO
    # =========================================================================

    def undo(self) -> Dict[str, Any]:
        """Undo the most recent change (atomic or grouped). Reverts files on disk."""
        if not self.undo_redo.can_undo():
            return {"success": False, "error": "Nothing to undo."}

        item = self.undo_redo.undo_stack.pop()
        self.undo_redo.redo_stack.append(item)

        reverted_files: List[str] = []

        if item["type"] == "atomic":
            change: ChangeRecord = item["data"]
            full_path = os.path.normpath(os.path.join(self.project_dir, change.file_path))
            if change.operation == "create":
                if os.path.exists(full_path):
                    os.remove(full_path)
            else:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as fp:
                    fp.write(change.before_content)
            reverted_files.append(change.file_path)

            return {
                "success": True,
                "type": "atomic",
                "change_id": change.change_id,
                "reverted_files": reverted_files,
                "author": change.author,
                "can_undo": self.undo_redo.can_undo(),
                "can_redo": self.undo_redo.can_redo()
            }

        elif item["type"] == "group":
            group: ChangeGroup = item["data"]
            group.status = "undone"
            # Revert in reverse order
            for change in reversed(group.changes):
                full_path = os.path.normpath(os.path.join(self.project_dir, change.file_path))
                if change.operation == "create":
                    if os.path.exists(full_path):
                        os.remove(full_path)
                else:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as fp:
                        fp.write(change.before_content)
                reverted_files.append(change.file_path)

            self.history_store.save_history(self.records, self.groups)

            return {
                "success": True,
                "type": "group",
                "group_id": group.group_id,
                "title": group.title,
                "reverted_files": list(dict.fromkeys(reverted_files)),
                "author": group.author,
                "can_undo": self.undo_redo.can_undo(),
                "can_redo": self.undo_redo.can_redo()
            }

        return {"success": False, "error": "Unknown undo item type."}

    def redo(self) -> Dict[str, Any]:
        """Redo the most recently undone change without re-calling LLM."""
        if not self.undo_redo.can_redo():
            return {"success": False, "error": "Nothing to redo."}

        item = self.undo_redo.redo_stack.pop()
        self.undo_redo.undo_stack.append(item)

        restored_files: List[str] = []

        if item["type"] == "atomic":
            change: ChangeRecord = item["data"]
            full_path = os.path.normpath(os.path.join(self.project_dir, change.file_path))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as fp:
                fp.write(change.after_content)
            restored_files.append(change.file_path)

            return {
                "success": True,
                "type": "atomic",
                "change_id": change.change_id,
                "restored_files": restored_files,
                "author": change.author,
                "can_undo": self.undo_redo.can_undo(),
                "can_redo": self.undo_redo.can_redo()
            }

        elif item["type"] == "group":
            group: ChangeGroup = item["data"]
            group.status = "applied"
            for change in group.changes:
                full_path = os.path.normpath(os.path.join(self.project_dir, change.file_path))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as fp:
                    fp.write(change.after_content)
                restored_files.append(change.file_path)

            self.history_store.save_history(self.records, self.groups)

            return {
                "success": True,
                "type": "group",
                "group_id": group.group_id,
                "title": group.title,
                "restored_files": list(dict.fromkeys(restored_files)),
                "author": group.author,
                "can_undo": self.undo_redo.can_undo(),
                "can_redo": self.undo_redo.can_redo()
            }

        return {"success": False, "error": "Unknown redo item type."}

    def undo_specific_group(self, group_id: str) -> Dict[str, Any]:
        """Revert an entire logical group by its ID."""
        target_group = next((g for g in self.groups if g.group_id == group_id), None)
        if not target_group:
            return {"success": False, "error": f"Group '{group_id}' not found."}

        reverted_files: List[str] = []
        for change in reversed(target_group.changes):
            full_path = os.path.normpath(os.path.join(self.project_dir, change.file_path))
            if change.operation == "create":
                if os.path.exists(full_path):
                    os.remove(full_path)
            else:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as fp:
                    fp.write(change.before_content)
            reverted_files.append(change.file_path)

        target_group.status = "undone"
        self.history_store.save_history(self.records, self.groups)

        return {
            "success": True,
            "group_id": group_id,
            "title": target_group.title,
            "reverted_files": list(dict.fromkeys(reverted_files))
        }

    # =========================================================================
    # TERMINAL EXECUTION TRACKING
    # =========================================================================

    def snapshot_filesystem_state(self) -> Dict[str, str]:
        """Capture hashes of all current files in the project."""
        manifest: Dict[str, str] = {}
        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                full_f = os.path.join(root, f)
                rel_f = os.path.relpath(full_f, self.project_dir)
                manifest[rel_f] = compute_file_sha256(full_f)
        return manifest

    def track_terminal_changes(self, before_manifest: Dict[str, str], command: str) -> List[ChangeRecord]:
        """Detect and log files created or modified by a terminal execution."""
        after_manifest = self.snapshot_filesystem_state()
        terminal_records: List[ChangeRecord] = []

        # Created or Modified
        for rel_p, curr_h in after_manifest.items():
            if rel_p not in before_manifest:
                # File created by terminal
                full_p = os.path.join(self.project_dir, rel_p)
                content = ""
                try:
                    with open(full_p, "r", encoding="utf-8", errors="replace") as fp:
                        content = fp.read()
                except Exception:
                    pass
                rec = ChangeRecord(
                    author="terminal",
                    operation="create",
                    file_path=rel_p,
                    before_content="",
                    after_content=content,
                    reason=f"Created by terminal command: {command}"
                )
                self.records.append(rec)
                terminal_records.append(rec)
            elif before_manifest[rel_p] != curr_h:
                # File modified by terminal
                full_p = os.path.join(self.project_dir, rel_p)
                content = ""
                try:
                    with open(full_p, "r", encoding="utf-8", errors="replace") as fp:
                        content = fp.read()
                except Exception:
                    pass
                rec = ChangeRecord(
                    author="terminal",
                    operation="modify",
                    file_path=rel_p,
                    before_content="",  # terminal before content not cached
                    after_content=content,
                    reason=f"Modified by terminal command: {command}"
                )
                self.records.append(rec)
                terminal_records.append(rec)

        if terminal_records:
            self.history_store.save_history(self.records, self.groups)

        return terminal_records

    # =========================================================================
    # QUERYING HISTORY & TIMELINE
    # =========================================================================

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Return combined chronological timeline of project history."""
        timeline: List[Dict[str, Any]] = []

        # Add groups
        for g in self.groups:
            timeline.append({
                "type": "group",
                "id": g.group_id,
                "title": g.title,
                "author": g.author,
                "timestamp": g.timestamp,
                "task_id": g.task_id,
                "why": g.why,
                "what": g.what,
                "risk_level": g.risk_level,
                "status": g.status,
                "file_count": len(g.changes),
                "files": [c.file_path for c in g.changes]
            })

        # Add atomic changes not in any group
        grouped_ids = {c.change_id for g in self.groups for c in g.changes}
        for r in self.records:
            if r.change_id not in grouped_ids:
                timeline.append({
                    "type": "atomic",
                    "id": r.change_id,
                    "title": f"Edited {r.file_path}",
                    "author": r.author,
                    "timestamp": r.timestamp,
                    "operation": r.operation,
                    "file_path": r.file_path,
                    "reason": r.reason,
                    "risk_level": r.risk_level,
                    "file_count": 1,
                    "files": [r.file_path]
                })

        timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return timeline

    def get_change_details(self, change_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details and diff of a specific atomic change."""
        for r in self.records:
            if r.change_id == change_id:
                return r.to_dict()
        return None

    def get_group_details(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details and grouped diff of a change group."""
        for g in self.groups:
            if g.group_id == group_id:
                return g.to_dict()
        return None


# Global cache of ChangeManagers keyed by canonical project directory
_CHANGE_MANAGERS: Dict[str, ChangeManager] = {}


def get_change_manager(project_dir: str) -> ChangeManager:
    """Retrieve or instantiate the ChangeManager for a workspace."""
    norm_dir = os.path.normpath(project_dir)
    if norm_dir not in _CHANGE_MANAGERS:
        _CHANGE_MANAGERS[norm_dir] = ChangeManager(norm_dir)
    return _CHANGE_MANAGERS[norm_dir]
