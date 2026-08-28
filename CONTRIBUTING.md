# Contributing to KritiAI

Thank you for your interest in contributing to KritiAI — the open-source, local-first Windows-native autonomous AI execution platform.

## Architecture Guidelines

1. **Modular Design**: Components under `core/`, `ai/`, `agents/`, `tools/`, `memory/`, and `security/` must remain loosely coupled.
2. **Never Bypass Security**:
   - Never allow LLM prompts to bypass the `PermissionEngine`.
   - Never disable the `EmergencyStopManager` or `VerificationEngine`.
   - Keep the AI process in user-space; never attempt direct kernel execution.
3. **Real Verification**:
   - Never mark an action complete merely because a command exited.
   - Always implement an independent `verify()` method for every tool.
4. **Local-First & Offline Resilience**:
   - Features must operate offline wherever the task does not strictly require internet access.
   - Do not introduce mandatory paid cloud dependencies.

## Development Workflow

### Setup

```bash
# Clone the repository
git clone https://github.com/atultiwari997721/Kernal_Level_RAG_and_IDE_Tooling_Interface_AI.git
cd Kernal_Level_RAG_and_IDE_Tooling_Interface_AI

# Install dependencies in editable mode
pip install -e .[dev,desktop]
```

### Running the Desktop App

```bash
# Using the Windows batch launcher
./kritiai.bat

# Or directly with Python
python -m apps.desktop.launcher
```

### Running Tests

```bash
python -m pytest tests -v
```

All contributions must pass the test suite and include unit/integration tests for any new features or tools.
