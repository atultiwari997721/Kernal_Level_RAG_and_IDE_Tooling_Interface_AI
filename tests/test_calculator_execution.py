"""Tests for End-to-End Calculator Scaffolding at Specific Location."""
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


def test_autonomous_create_calculator_at_specific_location(tmp_path: Path):
    calc_dir = tmp_path / "MyCalculatorApp"

    db_conn = DatabaseConnection(db_path=tmp_path / "test_calc.db")
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

    goal = f"Create a calculator in {str(calc_dir)}"
    result = orchestrator.run_goal(goal=goal)

    assert result["success"] is True
    assert result["status"] == TaskState.COMPLETED.value

    # Verify directory created at exact location
    assert calc_dir.is_dir()

    # Verify calculator.html exists and is complete
    html_file = calc_dir / "calculator.html"
    assert html_file.is_file()
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
        assert "<title>Modern Calculator" in html_content
        assert "function calculate()" in html_content

    # Verify calculator.py exists and has Tkinter GUI
    py_file = calc_dir / "calculator.py"
    assert py_file.is_file()
    with open(py_file, "r", encoding="utf-8") as f:
        py_content = f.read()
        assert "class CalculatorApp" in py_content
        assert "tkinter" in py_content

    # Verify run_calculator.bat launcher exists
    bat_file = calc_dir / "run_calculator.bat"
    assert bat_file.is_file()
