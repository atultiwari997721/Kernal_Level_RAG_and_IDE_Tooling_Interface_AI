"""Deterministic Permission Engine for KritiAI."""
from typing import Optional, Set
from config.settings import AppConfig, PowerMode, get_config
from security.policies.models import PermissionDecision, PolicyEvaluation, RiskLevel


class PermissionEngine:
    """Evaluates tool execution requests deterministically independent of LLM prompts."""

    def __init__(self, config: Optional[AppConfig] = None):
        self._config = config
        self._always_allowed_actions: Set[str] = set()

    @property
    def config(self) -> AppConfig:
        return self._config or get_config()

    def allow_action_permanently(self, tool_name: str, action: str) -> None:
        """User chose 'Always Allow This Type'."""
        self._always_allowed_actions.add(f"{tool_name}:{action}")

    def evaluate(
        self,
        tool_name: str,
        action: str,
        risk_level: RiskLevel,
        target: Optional[str] = None,
        required_permission: Optional[str] = None,
        power_mode_override: Optional[PowerMode] = None
    ) -> PolicyEvaluation:
        """Deterministically determine if an action should be allowed, denied, or prompt user."""
        cfg = self.config
        power_mode = power_mode_override or cfg.power_mode

        # Check Emergency Stop
        if getattr(cfg, "emergency_stop_active", False):
            return PolicyEvaluation(
                decision=PermissionDecision.DENY,
                reason="Emergency STOP is active. All actions are blocked.",
                risk_level=risk_level,
                tool_name=tool_name,
                action=action,
                target=target
            )

        # Check Granular Permission toggles
        if required_permission:
            perm_enabled = getattr(cfg.permissions, required_permission, True)
            if not perm_enabled:
                return PolicyEvaluation(
                    decision=PermissionDecision.DENY,
                    reason=f"Granular permission '{required_permission}' is disabled in settings.",
                    risk_level=risk_level,
                    tool_name=tool_name,
                    action=action,
                    target=target
                )

        # Check if user previously marked this action as permanently allowed
        action_key = f"{tool_name}:{action}"
        if action_key in self._always_allowed_actions:
            return PolicyEvaluation(
                decision=PermissionDecision.ALLOW,
                reason=f"Action '{action_key}' was previously allowed by user preference.",
                risk_level=risk_level,
                tool_name=tool_name,
                action=action,
                target=target
            )

        # 1. RISK MODE: Maximum configured autonomy
        if power_mode == PowerMode.RISK:
            if risk_level == RiskLevel.CRITICAL and target and ("C:\\Windows" in target or "System32" in target):
                return PolicyEvaluation(
                    decision=PermissionDecision.ASK_USER,
                    reason="Critical system directory targeted even in Risk Mode.",
                    risk_level=risk_level,
                    tool_name=tool_name,
                    action=action,
                    target=target,
                    requires_approval_prompt=f"KritiAI wants to perform critical action on {target}. Allow?"
                )
            return PolicyEvaluation(
                decision=PermissionDecision.ALLOW,
                reason="Allowed under Risk Mode autonomy policy.",
                risk_level=risk_level,
                tool_name=tool_name,
                action=action,
                target=target
            )

        # 2. AUTONOMOUS MODE (Default): Normal workflow actions proceed automatically
        if power_mode == PowerMode.AUTONOMOUS:
            if risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM):
                return PolicyEvaluation(
                    decision=PermissionDecision.ALLOW,
                    reason="Allowed under Autonomous Mode for low/medium risk actions.",
                    risk_level=risk_level,
                    tool_name=tool_name,
                    action=action,
                    target=target
                )
            elif risk_level == RiskLevel.HIGH:
                # In Autonomous mode, file deletions or destructive actions prompt user
                return PolicyEvaluation(
                    decision=PermissionDecision.ASK_USER,
                    reason=f"High-risk action '{action}' requires user confirmation under Autonomous policy.",
                    risk_level=risk_level,
                    tool_name=tool_name,
                    action=action,
                    target=target,
                    requires_approval_prompt=f"KritiAI wants to {action} on {target or tool_name}. Allow?"
                )
            else:  # CRITICAL
                return PolicyEvaluation(
                    decision=PermissionDecision.ASK_USER,
                    reason="Critical action requires explicit user confirmation.",
                    risk_level=risk_level,
                    tool_name=tool_name,
                    action=action,
                    target=target,
                    requires_approval_prompt=f"CRITICAL ACTION: KritiAI wants to {action} on {target}. Confirm?"
                )

        # 3. SAFE MODE: Maximum user approval for any side effects
        if power_mode == PowerMode.SAFE:
            if risk_level == RiskLevel.LOW:
                # Read-only operations are permitted
                return PolicyEvaluation(
                    decision=PermissionDecision.ALLOW,
                    reason="Read-only operation allowed in Safe Mode.",
                    risk_level=risk_level,
                    tool_name=tool_name,
                    action=action,
                    target=target
                )
            else:
                return PolicyEvaluation(
                    decision=PermissionDecision.ASK_USER,
                    reason=f"Safe Mode requires user approval for state-altering action '{action}'.",
                    risk_level=risk_level,
                    tool_name=tool_name,
                    action=action,
                    target=target,
                    requires_approval_prompt=f"Safe Mode: KritiAI wants to execute {tool_name} ({action}) on {target or 'system'}. Allow?"
                )

        # Fallback safe default
        return PolicyEvaluation(
            decision=PermissionDecision.ASK_USER,
            reason="Unrecognized power mode; defaulting to safe confirmation.",
            risk_level=risk_level,
            tool_name=tool_name,
            action=action,
            target=target,
            requires_approval_prompt=f"Allow {tool_name}:{action}?"
        )
