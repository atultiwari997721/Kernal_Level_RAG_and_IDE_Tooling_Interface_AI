"""Tests for KritiAI Deterministic Permission Engine."""
from config.settings import AppConfig, GranularPermissions, PowerMode
from security.permissions.engine import PermissionEngine
from security.policies.models import PermissionDecision, RiskLevel


def test_autonomous_mode_permissions():
    cfg = AppConfig(power_mode=PowerMode.AUTONOMOUS)
    engine = PermissionEngine(cfg)

    # Low & Medium risk actions should be automatically allowed (zero user interaction)
    eval_create = engine.evaluate("filesystem", "create_folder", RiskLevel.MEDIUM, target="Test")
    assert eval_create.decision == PermissionDecision.ALLOW

    eval_read = engine.evaluate("filesystem", "read_file", RiskLevel.LOW, target="doc.txt")
    assert eval_read.decision == PermissionDecision.ALLOW

    # High-risk actions in Autonomous Mode should ask the user
    eval_delete = engine.evaluate("filesystem", "delete", RiskLevel.HIGH, target="important.db")
    assert eval_delete.decision == PermissionDecision.ASK_USER


def test_safe_mode_permissions():
    cfg = AppConfig(power_mode=PowerMode.SAFE)
    engine = PermissionEngine(cfg)

    # Read-only allowed
    eval_read = engine.evaluate("filesystem", "read_file", RiskLevel.LOW, target="file.txt")
    assert eval_read.decision == PermissionDecision.ALLOW

    # Side-effects ask user
    eval_create = engine.evaluate("filesystem", "create_folder", RiskLevel.MEDIUM, target="Test")
    assert eval_create.decision == PermissionDecision.ASK_USER


def test_risk_mode_permissions():
    cfg = AppConfig(power_mode=PowerMode.RISK)
    engine = PermissionEngine(cfg)

    eval_delete = engine.evaluate("filesystem", "delete", RiskLevel.HIGH, target="temp.txt")
    assert eval_delete.decision == PermissionDecision.ALLOW


def test_granular_permission_toggle():
    perms = GranularPermissions(allow_filesystem=False)
    cfg = AppConfig(permissions=perms)
    engine = PermissionEngine(cfg)

    eval_fs = engine.evaluate("filesystem", "create_folder", RiskLevel.MEDIUM, required_permission="allow_filesystem")
    assert eval_fs.decision == PermissionDecision.DENY
    assert "disabled in settings" in eval_fs.reason
