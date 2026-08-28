# KritiAI 🤖⚡
### Open-Source Local-First Autonomous AI Execution Platform for Windows

[![Windows 10/11 Native](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com/windows)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests: Passing](https://img.shields.io/badge/Tests-21%20Passed-10b981.svg)]()

> **From user idea to real-world verified execution on Windows — with zero unnecessary interaction.**

KritiAI is NOT merely a chatbot. It is a personal AI execution layer operating natively on Windows 10 & 11. It allows you to give an AI a high-level goal and have it understand the objective, recall context, plan steps, select models/agents/tools, enforce security policies, execute commands on Windows, observe real-world outcomes, verify results, self-correct failures, and report accomplishments.

---

## 🏗️ Architecture In One Picture

```text
                     ┌───────────────────┐
                     │       USER        │
                     └─────────┬─────────┘
                               │
                      ┌────────▼────────┐
                      │   KRITIAI UI    │
                      └────────┬────────┘
                               │
               ┌───────────────┴───────────────┐
               │                               │
          CHAT MODE                       KRITIMODE
               │                               │
               └───────────────┬───────────────┘
                               │
                      ┌────────▼─────────┐
                      │   GOAL ENGINE    │
                      └────────┬─────────┘
                               │
                      ┌────────▼─────────┐
                      │  MEMORY + RAG    │
                      └────────┬─────────┘
                               │
                      ┌────────▼─────────┐
                      │  ORCHESTRATOR    │
                      └────────┬─────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
    ┌──────────┐         ┌──────────┐         ┌──────────┐
    │ PLANNER  │         │  MODEL   │         │  AGENT   │
    │          │         │  ROUTER  │         │ MANAGER  │
    └────┬─────┘         └────┬─────┘         └────┬─────┘
         └─────────────────────┼─────────────────────┘
                               ▼
                      ┌─────────────────┐
                      │ POLICY ENGINE   │
                      │ Safe            │
                      │ Autonomous      │
                      │ Risk            │
                      └────────┬────────┘
                               ▼
                      ┌─────────────────┐
                      │  TASK ENGINE    │
                      └────────┬────────┘
                               ▼
                      ┌─────────────────┐
                      │  TOOL EXECUTOR  │
                      └────────┬────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
     WINDOWS                BROWSER               DEV
         │                     │                     │
         ▼                     ▼                     ▼
    Applications          Websites              Code
    Files                 UI                    Git
    Keyboard              Vision                GitHub
    Mouse                 Screenshots           Docker
    Terminal              Forms                 Deploy
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
                      ┌─────────────────┐
                      │   OBSERVER      │
                      └────────┬────────┘
                               ▼
                      ┌─────────────────┐
                      │   VERIFIER      │
                      └────────┬────────┘
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
                  SUCCESS              ERROR
                     │                   │
                     ▼                   ▼
                 COMPLETE             RECOVER
                                         │
                                         ▼
                                      RETRY
                                         │
                                         └──────► EXECUTE
```

---

## ⚡ Primary Power Modes

| Power Mode | Autonomy Level | Behavior |
| :--- | :--- | :--- |
| **AUTONOMOUS** *(Default)* | **Frictionless Autonomy** | Executes normal workflow actions (create folders/files, dev commands, read files, run tests, verify) **without prompting the user**. Asks only when blocked, ambiguous, or encountering critical system actions. |
| **SAFE** | **Maximum Approval** | Prompts the user before any state-altering action on the computer. Displays intent, affected resources, and requests approval (`Allow Once`, `Always Allow`, `Deny`). |
| **RISK** | **Maximum Autonomy** | Allows full execution without confirmation, protected by watchdog timers, resource limits, tamper-evident audit logs, and an independent **Emergency STOP**. |

---

## 🌟 KritiAI v0.1 Milestone Verified

KritiAI v0.1 ships with complete implementation of the end-to-end execution loop:

```text
Windows Desktop App (Edge App Mode / Fluent Dark Theme)
   ↓
Chat Mode + KritiMode Execution Dashboard
   ↓
Local Offline Rule/Intent Intelligence + Local Ollama + Cloud API Gateway
   ↓
Model Gateway & Intelligent Model Router
   ↓
Multi-Tier Memory (Conversation, User, Project, Task, Long-Term + Local Vector Store)
   ↓
Standardized Tool Subsystem (Filesystem, Terminal, PowerShell, CMD, Process Manager, Apps, System Info)
   ↓
Safe / Autonomous (Default) / Risk Policy Engine
   ↓
KritiMode Autonomous Orchestrator
   ↓
User Goal: "Create a folder called Test"
   ↓
KritiAI parses intent → plans step → routes model → checks policy → executes FilesystemTool
   ↓
Verifies physical creation on Windows filesystem
   ↓
Reports verified success with ZERO user interaction
```

---

## 📦 Project Structure

```text
KritiAI/
├── apps/
│   └── desktop/                  # Windows Desktop frontend & launcher
│       ├── static/               # Windows 11 Fluent Dark UI (HTML/CSS/JS)
│       ├── server.py             # FastAPI backend with WebSockets
│       └── launcher.py           # Native window desktop launcher (Edge/Chrome App)
├── core/
│   ├── orchestrator/             # Central execution coordinator
│   ├── planner/                  # Goal decomposition & step generation
│   ├── task_engine/              # Task lifecycle manager
│   ├── goal_engine/              # Natural language goal understanding
│   ├── state_machine/            # Deterministic Task State Machine
│   ├── verification/             # Independent outcome verification
│   └── recovery/                 # Self-correction & diagnostic engine
├── ai/
│   ├── gateway/                  # Provider-independent Model Gateway
│   ├── router/                   # Intelligent Model Router
│   └── providers/                # Offline local, Ollama, and OpenAI-compatible
├── agents/                       # Specialized autonomous agents
│   ├── base.py                   # Agent contract
│   ├── filesystem.py             # File and folder operations
│   ├── windows.py                # Windows automation and application control
│   ├── coding.py                 # Dev execution and terminal commands
│   ├── verification.py           # Action verification agent
│   └── manager.py                # Agent manager and dispatcher
├── tools/                        # Standardized tool execution layer
│   ├── base.py                   # BaseTool definition
│   ├── registry.py               # Tool Registry with policy & dry-run
│   ├── filesystem/               # FilesystemTool (create, read, write, edit, delete, list, search)
│   ├── terminal/                 # PowerShellTool, CmdTool, CommandRunner, Safety Classifier
│   ├── windows/                  # AppManager, ProcessManager, SystemInfo, Clipboard, UIAutomation
│   └── screenshot/               # ScreenshotTool (full screen, region)
├── memory/                       # Local-first memory system
│   ├── base.py                   # Memory models
│   ├── vector_store.py           # Zero-dependency local TF-IDF vector search
│   └── manager.py                # Multi-tier memory coordinator
├── security/                     # Security & permission boundaries
│   ├── policies/                 # RiskLevel, PermissionDecision, PolicyEvaluation
│   ├── permissions/              # Deterministic Permission Engine
│   ├── audit/                    # Tamper-evident persistent action audit trail
│   ├── sandbox/                  # Watchdog timer & Emergency STOP controller
│   └── privileged/               # Windows UAC elevation interface (user-space isolation)
├── database/                     # Local SQLite database
│   ├── connection.py             # Thread-safe SQLite connection pooling
│   ├── schema.py                 # DDL definitions (tasks, sessions, memory, audit)
│   └── repository.py             # Persistent CRUD repository
├── config/                       # Centralized configuration system
│   └── settings.py               # Pydantic-based configuration model & loader
├── tests/                        # 21 automated unit & integration tests
│   ├── test_state_machine.py     # State machine validation
│   ├── test_permission_engine.py # Safe/Autonomous/Risk permission tests
│   ├── test_tools.py             # Tool execution & real-world verification tests
│   ├── test_model_gateway.py     # Model gateway & routing tests
│   ├── test_memory.py            # Memory storage & vector search tests
│   ├── test_orchestrator.py      # End-to-end autonomous execution tests
│   └── test_api_server.py        # REST API & WebSocket tests
├── kritiai.bat                   # 1-click Windows batch launcher
├── kritiai.ps1                   # 1-click PowerShell launcher
├── pyproject.toml                # Project metadata & dependencies
├── LICENSE                       # Apache 2.0
├── SECURITY.md                   # Security principles and vulnerability policy
└── CONTRIBUTING.md               # Contribution guidelines
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Windows 10 or Windows 11
- Python 3.10+ installed

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/atultiwari997721/Kernal_Level_RAG_and_IDE_Tooling_Interface_AI.git
cd Kernal_Level_RAG_and_IDE_Tooling_Interface_AI

# Install dependencies in editable mode
pip install -e .
```

### 3. Launching KritiAI
You can start the desktop application with a single double-click on `kritiai.bat`, or from the terminal:
```powershell
# Launch with Windows 11 Native Edge App Window
./kritiai.bat

# Or run directly via Python
python -m apps.desktop.launcher
```

This launches the local execution server on `http://127.0.0.1:8765` and opens a borderless desktop window.

### 4. Running the Test Suite
```powershell
python -m pytest tests -v
```

---

## 🛡️ Security Architecture

1. **User-Space Isolation**: KritiAI never runs within the Windows kernel.
2. **Deterministic Permission Engine**: Security decisions are evaluated by deterministic Python code, never by prompt instructions alone.
3. **Emergency STOP Watchdog**: An independent process supervisor tracks spawned subprocess PIDs and terminates them immediately when the red Emergency STOP button is pressed.
4. **Offline First**: All core planning, execution, memory, and database capabilities operate without an internet connection or paid API keys.

---

## 📄 License

KritiAI is open-source software licensed under the **[Apache License 2.0](LICENSE)**.
