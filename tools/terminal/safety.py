"""Deterministic Command Safety and Risk Classification for Windows Execution."""
import re
from typing import Dict, List, Tuple
from security.policies.models import RiskLevel

SAFE_PATTERNS = [
    r"^(dir|ls|Get-ChildItem|gci)(\s|$)",
    r"^(type|cat|Get-Content|gc)(\s|$)",
    r"^(echo|Write-Output)(\s|$)",
    r"^(git\s+(status|log|branch|diff|remote|show))(\s|$)",
    r"^(python|py|node|npm|git|cargo|go|rustc)\s+(--version|-v|--help|-h)(\s|$)",
    r"^(Get-Process|ps|tasklist)(\s|$)",
    r"^(whoami|hostname|ipconfig|systeminfo)(\s|$)",
    r"^(pwd|cd|Get-Location)(\s|$)",
]

DESTRUCTIVE_PATTERNS = [
    r"rmdir\s+.*(/s|/q)",
    r"del\s+.*(/f|/s|/q)",
    r"Remove-Item\s+.*(-Recurse|-Force)",
    r"Clear-Disk",
    r"Format-Volume",
    r"Stop-Computer",
    r"Restart-Computer",
    r"Drop-Database",
]

CRITICAL_PATTERNS = [
    r"diskpart(\s|$)",
    r"bcdedit(\s|$)",
    r"reg\s+delete\s+HKLM",
    r"takeown\s+/f\s+C:\\Windows",
    r"icacls\s+C:\\Windows",
    r"Set-ExecutionPolicy\s+Unrestricted\s+-Scope\s+LocalMachine",
    r"format\s+[A-Za-z]:",
]

PRIVILEGED_PATTERNS = [
    r"net\s+user(\s|$)",
    r"net\s+localgroup(\s|$)",
    r"sc\s+(create|delete|config)(\s|$)",
    r"Install-WindowsFeature",
    r"Enable-WindowsOptionalFeature",
]


class CommandSafetyClassifier:
    """Classifies commands deterministically into Risk Levels."""

    @classmethod
    def classify(cls, command: str) -> Tuple[RiskLevel, str]:
        cmd = command.strip()
        
        # Check Critical Patterns
        for pat in CRITICAL_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return RiskLevel.CRITICAL, f"Command matches critical system pattern: {pat}"

        # Check Privileged Patterns
        for pat in PRIVILEGED_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return RiskLevel.HIGH, f"Command requires administrative privilege: {pat}"

        # Check Destructive Patterns
        for pat in DESTRUCTIVE_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return RiskLevel.HIGH, f"Command contains destructive operations: {pat}"

        # Check Safe Patterns
        for pat in SAFE_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return RiskLevel.LOW, "Read-only or status query command."

        # Default for normal execution (e.g. build, test, pip install, git commit)
        return RiskLevel.MEDIUM, "Standard development / execution command."
