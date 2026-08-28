# Security Policy for KritiAI

## Core Security Principles

1. **The LLM is NOT a Security Boundary**: Model outputs are treated as untrusted proposals. All permissions, validation, timeouts, resource limits, and execution safety are enforced strictly by deterministic application code.
2. **User-Space Isolation**: KritiAI executes entirely within Windows user space. The AI engine is never granted direct kernel access.
3. **Deterministic Permission Engine**: Every tool action passes through the Permission Engine before execution:
   - **Safe Mode**: Requires explicit user approval for any state-altering operations.
   - **Autonomous Mode (Default)**: Automatically permits safe and normal development/filesystem workflows, but prompts for destructive or critical actions.
   - **Risk Mode**: Grants maximum configured autonomy while preserving timeouts, audit logs, and the Emergency STOP watchdog.
4. **Independent Emergency STOP**: A dedicated hardware-level process supervisor monitors and registers all spawned subprocesses. Triggering Emergency STOP halts task scheduling and immediately terminates active child processes.
5. **No Secret Leakage**: Secrets and API keys are stored in secure local credential storage and are never printed to terminal logs, committed to Git, or sent to external model prompts unnecessarily.

## Reporting a Vulnerability

If you discover a security issue or vulnerability in KritiAI:
- Please do **NOT** open a public issue on GitHub.
- Instead, report it privately to the maintainers or via GitHub Security Advisories.
- Include reproduction steps, environment details, and risk assessment.
- The team will acknowledge receipt within 48 hours and work with you on a patch.
