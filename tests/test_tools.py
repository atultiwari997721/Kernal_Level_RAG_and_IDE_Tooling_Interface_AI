"""Tests for Standardized Tools with Automatic Real-World Verification."""
from pathlib import Path
from tools.filesystem.fs_tool import FilesystemTool
from tools.terminal.safety import CommandSafetyClassifier
from tools.terminal.runner import CommandRunner
from tools.windows.system_info import SystemInfoTool
from security.policies.models import RiskLevel


def test_filesystem_create_and_verify(tmp_path: Path):
    tool = FilesystemTool()

    # 1. Create Folder
    folder_path = tmp_path / "SubFolder"
    res_folder = tool.execute(operation="create_folder", path=str(folder_path))
    assert res_folder.success is True
    assert res_folder.verification["verified"] is True
    assert folder_path.is_dir()

    # 2. Create / Write File
    file_path = folder_path / "test.txt"
    res_file = tool.execute(operation="create_file", path=str(file_path), content="KritiAI Verified Content")
    assert res_file.success is True
    assert res_file.verification["verified"] is True
    assert file_path.is_file()

    # 3. Read File
    res_read = tool.execute(operation="read_file", path=str(file_path))
    assert res_read.success is True
    assert "KritiAI Verified Content" in res_read.data["content"]

    # 4. Delete File
    res_del = tool.execute(operation="delete", path=str(file_path))
    assert res_del.success is True
    assert res_del.verification["verified"] is True
    assert not file_path.exists()


def test_command_safety_classifier():
    # Safe
    risk_safe, _ = CommandSafetyClassifier.classify("git status")
    assert risk_safe == RiskLevel.LOW

    # Destructive
    risk_dest, _ = CommandSafetyClassifier.classify("del /f /s /q test.txt")
    assert risk_dest == RiskLevel.HIGH

    # Critical
    risk_crit, _ = CommandSafetyClassifier.classify("bcdedit /deletevalue")
    assert risk_crit == RiskLevel.CRITICAL


def test_command_runner_execution(tmp_path: Path):
    result = CommandRunner.execute(
        command="echo Hello_KritiAI",
        shell="powershell",
        working_directory=str(tmp_path)
    )
    assert result["status"] == "SUCCESS"
    assert result["exit_code"] == 0
    assert "Hello_KritiAI" in result["stdout"]


def test_system_info_hardware_detection():
    tool = SystemInfoTool()
    res = tool.execute()
    assert res.success is True
    assert "os" in res.data
    assert "memory_gb" in res.data
    assert "recommended_model_tier" in res.data
