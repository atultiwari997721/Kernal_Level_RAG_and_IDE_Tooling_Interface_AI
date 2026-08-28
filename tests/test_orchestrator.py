"""End-to-end Autonomous Execution Tests for KritiAI Orchestrator."""
import os
from pathlib import Path
from config.settings import AppConfig, PowerMode
from core.orchestrator.orchestrator import AIOrchestrator
from core.state_machine.states import TaskState
from core.task_engine.engine import TaskEngine
from database.connection import DatabaseConnection
from database.repository import Repository
from memory.manager import MemoryManager
from security.audit.logger import AuditLogger
from tools.registry import ToolRegistry


def test_autonomous_create_folder_milestone(tmp_path: Path):
    """Verifies the core milestone: 'Create a folder called Test' with zero user interaction in Autonomous Mode."""
    db_conn = DatabaseConnection(db_path=tmp_path / "test_orchestrator.db")
    repo = Repository(db=db_conn)
    audit = AuditLogger(repo=repo)

    config = AppConfig(
        power_mode=PowerMode.AUTONOMOUS,
        workspace_dir=tmp_path
    )
    tools = ToolRegistry(config=config, audit_logger=audit)
    task_engine = TaskEngine(repo=repo)
    memory_mgr = MemoryManager(repo=repo)

    orchestrator = AIOrchestrator(
        config=config,
        task_engine=task_engine,
        tool_registry=tools,
        memory_manager=memory_mgr
    )

    # Execute milestone with zero user interaction
    goal = "Create a folder called Test"
    result = orchestrator.run_goal(goal=goal)

    assert result["success"] is True
    assert result["status"] == TaskState.COMPLETED.value
    assert "Test" in result["final_result"]

    # Verify physical real-world effect on Windows filesystem
    expected_folder = tmp_path / "Test"
    assert expected_folder.is_dir()

    # Verify audit trail was logged
    audit_logs = repo.get_audit_logs(task_id=result["task_id"])
    assert len(audit_logs) > 0
    assert audit_logs[0]["decision"] == "allow"
    assert audit_logs[0]["tool"] == "filesystem"


def test_autonomous_create_file_with_content(tmp_path: Path):
    """Verifies creating a file with content and checking verified results."""
    db_conn = DatabaseConnection(db_path=tmp_path / "test_file_exec.db")
    repo = Repository(db=db_conn)
    audit = AuditLogger(repo=repo)

    config = AppConfig(
        power_mode=PowerMode.AUTONOMOUS,
        workspace_dir=tmp_path
    )
    tools = ToolRegistry(config=config, audit_logger=audit)
    task_engine = TaskEngine(repo=repo)
    memory_mgr = MemoryManager(repo=repo)

    orchestrator = AIOrchestrator(
        config=config,
        task_engine=task_engine,
        tool_registry=tools,
        memory_manager=memory_mgr
    )

    goal = "Create a file called notes.txt with content Hello KritiAI"
    result = orchestrator.run_goal(goal=goal)

    assert result["success"] is True
    assert result["status"] == TaskState.COMPLETED.value

    # Verify file physically exists and content matches
    target_file = tmp_path / "notes.txt"
    assert target_file.is_file()
    with open(target_file, "r", encoding="utf-8") as f:
        assert f.read() == "Hello KritiAI"
