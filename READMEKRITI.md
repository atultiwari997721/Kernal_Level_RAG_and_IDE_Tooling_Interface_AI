# KritiAI 🤖

## Your Personal AI Assistant & Execution Layer for Windows

> **From an idea to execution — KritiAI helps you do it.**

KritiAI is an **open-source, local-first AI assistant and execution platform for Windows**.

Unlike a traditional chatbot that only generates answers, KritiAI is designed to understand a user's goal, plan the required steps, select the appropriate AI model and tools, execute actions on the computer, observe the results, verify completion, recover from failures, and continue until the task is completed or user input is genuinely required.

KritiAI is designed to run primarily on the user's own Windows computer.

It supports:

* Local LLMs
* Optional external AI APIs
* Local memory
* Local RAG
* Windows automation
* Terminal execution
* PowerShell
* CMD
* Browser automation
* Filesystem operations
* Application control
* Development tools
* Git/GitHub
* Autonomous workflows
* Multiple AI agents
* Automatic model selection

---

# 📌 Project Status

🚧 **KritiAI is currently under active development.**

The architecture described in this README represents the project's intended direction.

Features should only be marked as completed after they are actually implemented and tested.

---

# 🚀 Vision

The goal of KritiAI is to create a **personal AI execution layer for Windows**.

Traditional AI:

```text
User
 ↓
Question
 ↓
AI Answer
 ↓
User manually performs the task
```

KritiAI:

```text
User Goal
    ↓
Understand
    ↓
Remember
    ↓
Plan
    ↓
Select Model
    ↓
Select Agent
    ↓
Select Tools
    ↓
Check Permissions
    ↓
Execute
    ↓
Observe
    ↓
Verify
    ↓
Correct / Recover
    ↓
Continue
    ↓
Complete
```

The long-term goal is:

> **Give KritiAI a goal, and let it figure out how to accomplish it.**

---

# ✨ Core Features

## 🧠 Personal AI

KritiAI is designed to:

* Understand natural language
* Maintain context
* Remember user preferences
* Understand goals
* Break complex goals into tasks
* Create execution plans
* Select models
* Select agents
* Select tools
* Execute workflows
* Analyze results
* Recover from failures

---

# 💬 Chat Mode

Chat Mode is the normal conversational interface.

Use it for:

* Questions
* Explanations
* Brainstorming
* Research
* Code generation
* Code analysis
* File analysis
* Planning
* Learning
* RAG
* General AI assistance

Example:

```text
User:
Explain how FastAPI works.

KritiAI:
[Provides explanation]
```

Chat Mode primarily focuses on conversation and assistance.

---

# ⚡ KritiMode

KritiMode is the **execution mode** of KritiAI.

Instead of telling KritiAI every individual step, the user gives it a goal.

Example:

```text
Create a React website for my project,
test it, fix the errors and push it to GitHub.
```

KritiAI can plan:

```text
Understand requirements
 ↓
Inspect project
 ↓
Create architecture
 ↓
Generate code
 ↓
Install dependencies
 ↓
Run application
 ↓
Run tests
 ↓
Detect errors
 ↓
Fix errors
 ↓
Test again
 ↓
Verify
 ↓
Git commit
 ↓
GitHub push
 ↓
Verify remote repository
 ↓
Report result
```

---

# 🎵 Example: "Play Sita Ram"

A simple Windows automation example:

```text
User:

Play Sita Ram
```

KritiAI should understand that the user wants to play a song/video.

Possible execution:

```text
Goal:
Play Sita Ram

        ↓

Understand intent

        ↓

Identify available browser/media application

        ↓

Open browser if necessary

        ↓

Open YouTube or configured music service

        ↓

Search:
"Sita Ram"

        ↓

Analyze search results

        ↓

Select the most appropriate result

        ↓

Click Play

        ↓

Observe the player

        ↓

Verify playback

        ↓

Done
```

The user should not have to manually:

```text
Open Chrome
 ↓
Open YouTube
 ↓
Type Sita Ram
 ↓
Search
 ↓
Find result
 ↓
Click video
 ↓
Play
```

KritiAI performs the workflow through its Windows and Browser Execution Layers.

If multiple results are ambiguous, KritiAI can ask:

```text
I found multiple results for "Sita Ram".

Which one do you want?

[Result 1]
[Result 2]
[Result 3]
```

---

# 🪟 Windows Computer Control

KritiAI is designed to interact with Windows through controlled tools.

Potential capabilities include:

* Windows Terminal
* PowerShell
* CMD
* Windows APIs
* Filesystem
* Applications
* Processes
* Browser
* Keyboard
* Mouse
* Clipboard
* Screenshots
* UI Automation
* Git
* GitHub
* Development environments

Architecture:

```text
User
 ↓
KritiAI
 ↓
Orchestrator
 ↓
Planner
 ↓
Permission Engine
 ↓
Execution Manager
 ↓
Windows Tool
 ↓
Windows
```

The LLM should never directly receive unrestricted operating-system access.

---

# 🖥️ Terminal Access

KritiAI includes a dedicated Windows Execution Layer.

It should support:

* PowerShell
* CMD
* Windows Terminal where appropriate
* Configurable shells
* Working directories
* Environment variables
* Standard input
* Standard output
* Standard error
* Exit codes
* Timeouts
* Process cancellation
* Streaming output

Example:

```text
User:

Create a Python project called TestAI and install FastAPI.
```

KritiAI:

```text
Create project directory
 ↓
Initialize project
 ↓
Create virtual environment
 ↓
Activate environment
 ↓
Install FastAPI
 ↓
Verify installation
 ↓
Report result
```

---

# 💻 PowerShell

PowerShell is a first-class execution tool.

It can be used for legitimate tasks such as:

* Creating files
* Editing files
* Creating directories
* Running development commands
* Installing dependencies
* Running tests
* Starting applications
* Inspecting processes
* System information
* Git operations
* Build operations
* Automation

All meaningful commands should pass through the Permission Engine.

---

# ⌨️ CMD

CMD should also be supported.

Users can configure their preferred shell:

```text
Settings
 → Terminal
 → Shell

PowerShell
CMD
Custom
```

---

# 🧩 Architecture

```text
                         USER
                           │
                           ▼
                   ┌──────────────┐
                   │   KRITIAI UI │
                   └──────┬───────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
        CHAT MODE                 KRITIMODE
             │                         │
             └────────────┬────────────┘
                          ▼
                  ┌───────────────┐
                  │   GOAL ENGINE │
                  └───────┬───────┘
                          ▼
                  ┌───────────────┐
                  │  MEMORY + RAG │
                  └───────┬───────┘
                          ▼
                  ┌───────────────┐
                  │ ORCHESTRATOR  │
                  └───────┬───────┘
                          ▼
                  ┌───────────────┐
                  │    PLANNER    │
                  └───────┬───────┘
                          ▼
                  ┌───────────────┐
                  │ MODEL ROUTER  │
                  └───────┬───────┘
                          ▼
                  ┌───────────────┐
                  │ AGENT MANAGER │
                  └───────┬───────┘
                          ▼
                  ┌───────────────┐
                  │ POLICY ENGINE │
                  └───────┬───────┘
                          ▼
                  ┌───────────────┐
                  │ TASK ENGINE   │
                  └───────┬───────┘
                          ▼
                  ┌───────────────┐
                  │ TOOL EXECUTOR │
                  └───────┬───────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       WINDOWS          BROWSER         DEVELOPER
          │               │                │
          ▼               ▼                ▼
      PowerShell       Browser          Code
      CMD              DOM              Git
      Files            Vision           GitHub
      Apps             UI               Docker
      Processes        Screenshots       Testing
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                   OBSERVATION
                          │
                          ▼
                    VERIFICATION
                          │
                    ┌─────┴─────┐
                    ▼           ▼
                 SUCCESS      FAILURE
                    │           │
                    ▼           ▼
                 COMPLETE    RECOVERY
                                │
                                ▼
                              RETRY
```

---

# 🧠 AI Model Architecture

KritiAI should not depend on a single AI model.

It should support:

## Local Models

* Local LLMs
* Coding models
* Reasoning models
* Vision models
* Embedding models
* Speech models

Local models should be preferred when appropriate.

---

# ☁️ External Model APIs

Users can optionally connect external model providers.

Configuration:

```text
Provider
API Endpoint
API Key
Model
Capabilities
Context Size
Cost
Speed
```

The user controls which providers are available.

API keys must never be:

* Hard-coded
* Committed to Git
* Printed in logs
* Exposed unnecessarily

---

# 🤖 Automatic Model Router

KritiAI should automatically select an appropriate model based on:

* Task
* Capability
* Quality
* Speed
* Cost
* Context length
* Hardware
* Availability
* Privacy
* User preference

Example:

```text
Simple question
 → Fast local model

Complex coding
 → Coding model

Complex reasoning
 → Reasoning model

Image analysis
 → Vision model

Private information
 → Prefer local model
```

The router should optimize:

```text
QUALITY
+
SPEED
+
COST
+
PRIVACY
```

---

# 🎛️ Manual Model Selection

Users can override automatic model routing.

Settings:

```text
General Model:
Auto

Coding Model:
Auto

Reasoning Model:
Auto

Vision Model:
Auto

Embedding Model:
Auto
```

If the user chooses a specific model:

```text
User-selected model
        ↓
Automatic routing disabled for that category
        ↓
Selected model used
```

KritiAI must respect the user's explicit model selection.

---

# 🔐 Three Power Modes

## 🟢 Safe Mode

Safe Mode asks before meaningful actions.

Examples:

```text
Create file
→ Ask if configured

Delete file
→ Ask

Run risky command
→ Ask

Install software
→ Ask

Push to GitHub
→ Ask
```

Safe Mode prioritizes user control.

---

# 🟡 Autonomous Mode

Autonomous Mode is the default mode.

KritiAI can perform normal authorized operations automatically.

It should ask only when:

* It is genuinely stuck
* Credentials are required
* CAPTCHA appears
* Human verification is required
* A critical decision cannot be determined safely
* User policy requires approval

Example:

```text
User:
Create and test my application.
```

KritiAI can:

```text
Inspect project
 ↓
Edit files
 ↓
Run commands
 ↓
Run tests
 ↓
Fix errors
 ↓
Run tests again
 ↓
Complete
```

without asking for every individual action.

---

# 🔴 Risk Mode

Risk Mode provides maximum configured autonomy.

Depending on user policies, KritiAI may perform high-impact actions such as:

* Create
* Edit
* Delete
* Run commands
* Install software
* Git commit
* Git push
* Publish
* Post
* Deploy
* Browser automation
* System operations

Risk Mode should still maintain:

* Emergency STOP
* Audit logs
* Timeouts
* Resource limits
* Permission architecture
* Recovery mechanisms

Risk Mode does not mean unrestricted kernel access.

---

# 🛑 Emergency STOP

KritiAI must have an Emergency STOP.

It should be accessible from:

* Main interface
* KritiMode
* System tray
* Optional global shortcut

When activated:

```text
Stop scheduler
 ↓
Cancel pending actions
 ↓
Stop KritiAI-controlled processes where possible
 ↓
Block new tool execution
 ↓
Cancel task
 ↓
Save audit information
```

The emergency stop must not depend on the AI.

---

# 🧠 Memory System

KritiAI should provide:

* Conversation memory
* User memory
* Project memory
* Task memory
* Long-term memory
* Workflow memory

Users should be able to:

* View memory
* Edit memory
* Delete memory
* Clear memory
* Disable memory
* Export memory

---

# 🔎 Local RAG

KritiAI should provide local Retrieval-Augmented Generation.

Pipeline:

```text
Document
 ↓
Parse
 ↓
Chunk
 ↓
Embed
 ↓
Store
 ↓
Retrieve
 ↓
Rerank
 ↓
Context
 ↓
Model
```

Potential sources:

* PDF
* DOCX
* TXT
* Markdown
* Code
* Local folders
* Notes
* Project files
* Documentation
* Conversations

---

# 👨‍💻 Developer Agent

KritiAI should eventually support:

```text
Idea
 ↓
Requirements
 ↓
Architecture
 ↓
Project Setup
 ↓
Code
 ↓
Dependencies
 ↓
Testing
 ↓
Debugging
 ↓
Refactoring
 ↓
Git
 ↓
GitHub
 ↓
Deployment
 ↓
Verification
```

Capabilities:

* Generate code
* Edit code
* Analyze code
* Debug
* Test
* Refactor
* Create projects
* Install dependencies
* Run builds
* Git
* GitHub
* Docker
* Deployment

---

# 🤖 Agent Architecture

Initial agents:

```text
PlannerAgent
ResearchAgent
CodingAgent
DebuggingAgent
TestingAgent
BrowserAgent
WindowsAgent
FileSystemAgent
GitAgent
GitHubAgent
DeploymentAgent
DocumentationAgent
VisionAgent
VerificationAgent
```

Each agent should define:

```text
Name
Description
Capabilities
Tools
Input Schema
Output Schema
Permissions
Risk Level
Failure Strategy
```

---

# 🧰 Tool Architecture

Tools should use standardized interfaces.

Each tool should define:

```text
tool_name
description
input_schema
output_schema
permissions
risk_level
timeout
execution_function
verification_method
```

The LLM must not receive unrestricted access to arbitrary application functions.

---

# 🔄 Execution Loop

Every autonomous task follows:

```text
GOAL
 ↓
PLAN
 ↓
SELECT MODEL
 ↓
SELECT AGENT
 ↓
SELECT TOOL
 ↓
CHECK PERMISSION
 ↓
EXECUTE
 ↓
OBSERVE
 ↓
VERIFY
 ↓
SUCCESS?
 ├── YES → NEXT STEP
 │
 └── NO
       ↓
     DIAGNOSE
       ↓
     RECOVER
       ↓
     RETRY
       ↓
     VERIFY
```

If recovery fails:

```text
Re-plan
 ↓
Continue
OR
Ask User
```

---

# ✅ Verification

KritiAI should verify important actions.

Examples:

```text
Create file
→ Check that file exists

Run build
→ Check build result

Deploy website
→ Check endpoint

Git push
→ Verify remote repository

Open application
→ Verify process/window

Play music
→ Verify player state
```

KritiAI should not assume an action succeeded merely because a command returned exit code `0`.

---

# 🛠️ Recovery

When something fails:

```text
Error
 ↓
Classify
 ↓
Diagnose
 ↓
Select recovery
 ↓
Apply fix
 ↓
Retry
 ↓
Verify
```

Possible recovery methods:

* Retry
* Alternative command
* Alternative tool
* Alternative model
* Alternative agent
* Modify input
* Re-plan
* Ask user

---

# 📋 Task Engine

Each autonomous task receives a unique ID.

Possible states:

```text
CREATED
UNDERSTANDING
PLANNING
WAITING_FOR_APPROVAL
EXECUTING
OBSERVING
VERIFYING
RECOVERING
WAITING_FOR_USER
PAUSED
CANCELLED
FAILED
COMPLETED
```

Tasks should support:

* Pause
* Resume
* Cancel
* Retry
* Recovery

---

# 🌐 Browser Automation

KritiAI should provide a Browser Agent capable of:

* Opening browsers
* Navigating websites
* Searching
* Clicking
* Typing
* Scrolling
* Reading pages
* Detecting page state
* Taking screenshots
* Interacting with forms
* Verifying results

Preferred order:

```text
Accessibility / DOM
 ↓
Semantic UI
 ↓
Vision
 ↓
Coordinates as fallback
```

---

# 👁️ Vision

Vision allows KritiAI to understand visual interfaces.

It can help identify:

* Buttons
* Menus
* Windows
* Inputs
* Dialogs
* Errors
* Browser state
* Application state

Pipeline:

```text
Screenshot
 ↓
Vision Model
 ↓
UI Understanding
 ↓
Action
 ↓
Verification
```

---

# 🔐 Windows Privileged Operations

KritiAI should not run the entire application as Administrator.

When an operation requires elevated privileges:

```text
Request
 ↓
Detect privilege requirement
 ↓
Policy Engine
 ↓
Approval if required
 ↓
Windows Elevation
 ↓
Execute
 ↓
Verify
```

Do not bypass Windows security mechanisms.

---

# ⚙️ Kernel-Level Architecture

KritiAI's main AI process should remain in user space.

Normal architecture:

```text
KritiAI
 ↓
Execution Manager
 ↓
Permission Engine
 ↓
Windows APIs
```

If a future feature genuinely requires privileged system functionality:

```text
KritiAI
 ↓
Execution Manager
 ↓
Permission Engine
 ↓
Privileged Windows Service
 ↓
Approved Operations
```

Only if genuinely required:

```text
Privileged Service
 ↓
Signed Driver
 ↓
Windows Kernel
```

The LLM must never receive unrestricted direct kernel access.

---

# 📁 Project Structure

```text
KritiAI/
│
├── apps/
│   └── desktop/
│
├── core/
│   ├── orchestrator/
│   ├── planner/
│   ├── goal_engine/
│   ├── task_engine/
│   ├── state_machine/
│   └── verification/
│
├── ai/
│   ├── gateway/
│   ├── router/
│   ├── providers/
│   ├── local/
│   ├── vision/
│   ├── embeddings/
│   └── speech/
│
├── agents/
│   ├── planner/
│   ├── coding/
│   ├── debugging/
│   ├── testing/
│   ├── browser/
│   ├── windows/
│   ├── filesystem/
│   ├── research/
│   ├── git/
│   ├── github/
│   ├── deployment/
│   ├── documentation/
│   └── verification/
│
├── tools/
│   ├── filesystem/
│   ├── terminal/
│   ├── powershell/
│   ├── browser/
│   ├── ui_automation/
│   ├── screenshot/
│   ├── keyboard/
│   ├── mouse/
│   ├── process/
│   ├── applications/
│   ├── git/
│   └── github/
│
├── memory/
│   ├── conversation/
│   ├── user/
│   ├── project/
│   ├── task/
│   ├── long_term/
│   └── vector/
│
├── rag/
│   ├── ingestion/
│   ├── parsing/
│   ├── chunking/
│   ├── embeddings/
│   ├── retrieval/
│   └── reranking/
│
├── security/
│   ├── permissions/
│   ├── policies/
│   ├── secrets/
│   ├── audit/
│   └── sandbox/
│
├── database/
├── scheduler/
├── plugins/
├── updater/
├── models/
├── config/
├── tests/
├── docs/
├── scripts/
│
├── .github/
│   └── workflows/
│
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── LICENSE
└── pyproject.toml
```

---

# 🛠️ Technology Direction

## AI / Backend

Potential technologies:

* Python
* FastAPI
* Local LLM runtimes
* RAG
* Agent workflows
* Typed tool interfaces

## Desktop

A Windows-compatible desktop application.

The desktop UI should remain separate from the AI core.

## Database

Prefer local technologies:

* SQLite
* Local vector storage

## Development

* Git
* GitHub
* VS Code
* Docker where useful
* GitHub Actions

The exact technology stack may evolve.

---

# 💻 How to Run KritiAI

> **Important:** The exact commands depend on the implementation. The following is the intended development workflow for the project structure described above.

## 1. Requirements

Recommended development environment:

```text
Windows 10/11
Python 3.11+
Git
Node.js LTS
npm
VS Code
```

Optional depending on the selected model/runtime:

```text
GPU
CUDA
Local LLM runtime
Docker
```

---

# 2. Clone the Repository

Open PowerShell:

```powershell
git clone https://github.com/YOUR_USERNAME/KritiAI.git
cd KritiAI
```

Replace:

```text
YOUR_USERNAME
```

with the actual GitHub username.

---

# 3. Create Python Virtual Environment

Inside the project directory:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

# 4. Install Python Dependencies

If the project uses `requirements.txt`:

```powershell
pip install -r requirements.txt
```

If the project uses `pyproject.toml`:

```powershell
pip install -e .
```

Upgrade pip first:

```powershell
python -m pip install --upgrade pip
```

---

# 5. Install Frontend Dependencies

If the desktop/frontend contains a Node project:

```powershell
cd apps\desktop
npm install
```

Return to the project root:

```powershell
cd ..\..
```

---

# 6. Configure Environment Variables

Create:

```text
.env
```

Example:

```env
APP_ENV=development

DATABASE_URL=sqlite:///./kritiai.db

DEFAULT_POWER_MODE=autonomous

DEFAULT_MODEL=auto

ENABLE_LOCAL_MODELS=true

ENABLE_CLOUD_MODELS=false

GITHUB_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

Do not commit `.env`.

Add it to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
node_modules/
dist/
build/
logs/
*.db
```

---

# 7. Start the Backend

From the project root:

```powershell
uvicorn backend.main:app --reload
```

If the backend package uses a different entry point, use the project's configured startup command.

Example:

```powershell
python -m backend
```

The development API may be available at:

```text
http://127.0.0.1:8000
```

---

# 8. Start the Frontend

Open another PowerShell window.

Navigate to:

```powershell
cd KritiAI\apps\desktop
```

Then:

```powershell
npm run dev
```

The desktop UI should start according to the selected desktop framework.

---

# 9. Start KritiAI

The intended production workflow should eventually be:

```text
Install KritiAI
 ↓
Start KritiAI
 ↓
Local AI Engine starts
 ↓
Memory database starts
 ↓
Tool system starts
 ↓
Permission Engine starts
 ↓
Model Manager detects models
 ↓
KritiAI UI opens
```

The user should not need to manually start multiple services in the final release.

---

# 🧠 Installing Local Models

KritiAI is designed to support local models through a model adapter layer.

The model system should eventually allow:

```text
Settings
 ↓
Models
 ↓
Local Models
 ↓
Detect / Add Model
```

Users should be able to configure:

```text
Model Name
Model Type
Runtime
Context Length
GPU Usage
Capabilities
```

Example categories:

```text
General
Coding
Reasoning
Vision
Embedding
Speech
```

---

# ☁️ Adding an API Model

Users can configure external models from:

```text
Settings
 ↓
Models
 ↓
Providers
 ↓
Add Provider
```

Configuration:

```text
Provider:
Custom

API URL:
...

API Key:
...

Model:
...

Capabilities:
...

Cost:
...

Speed:
...
```

KritiAI's Model Router can then consider the provider automatically.

---

# ⚙️ Initial Settings

Recommended defaults:

```text
Power Mode:
Autonomous

Model:
Auto

Prefer Local Models:
Enabled

Cloud Models:
Disabled until configured

Memory:
Enabled

RAG:
Enabled

Automatic Updates:
Enabled

Telemetry:
Disabled by default
```

The user can change these settings.

---

# 🔄 Updating KritiAI

KritiAI is intended to be distributed through GitHub rather than requiring Microsoft Store distribution.

The application should periodically check GitHub Releases.

Architecture:

```text
KritiAI
 ↓
Update Manager
 ↓
Check GitHub Release
 ↓
Compare Versions
 ↓
New Version?
 ↓
Notify User
 ↓
Download
 ↓
Verify
 ↓
Install
 ↓
Restart
 ↓
Health Check
```

For developers:

```powershell
git pull
```

Then install any updated dependencies:

```powershell
pip install -r requirements.txt
```

and:

```powershell
npm install
```

when applicable.

---

# 📴 Offline Mode

KritiAI should continue working without Internet when the required functionality is local.

| Capability         | Offline |
| ------------------ | ------: |
| Local LLM          |       ✅ |
| Local RAG          |       ✅ |
| Local Memory       |       ✅ |
| Filesystem         |       ✅ |
| Terminal           |       ✅ |
| PowerShell         |       ✅ |
| CMD                |       ✅ |
| Windows Automation |       ✅ |
| Local Coding       |       ✅ |
| Git                |       ✅ |
| GitHub Remote      |       ❌ |
| Web Research       |       ❌ |
| Cloud Models       |       ❌ |
| Update Checking    |       ❌ |

---

# 🔒 Privacy

KritiAI follows a local-first privacy philosophy.

Users should be able to configure:

```text
Prefer Local Models
Never Send Local Files to Cloud
Ask Before Cloud Processing
Disable Cloud Providers
```

The application should clearly indicate when information is being sent to an external provider.

---

# 🔐 Security

The following must never depend solely on an LLM prompt:

* Authentication
* Authorization
* Permissions
* Secrets
* Privilege escalation
* Emergency STOP
* Tool authorization
* Update verification
* Security policies

These must be enforced through application code.

The LLM is an intelligence component.

It is **not** the security boundary.

---

# 🧪 Testing

Every feature should be tested before being marked complete.

Testing should include:

```text
Unit Tests
Integration Tests
Tool Tests
Agent Tests
Model Tests
Windows Automation Tests
Permission Tests
Recovery Tests
UI Tests
End-to-End Tests
```

Windows execution tests should use safe test environments whenever possible.

Never use production/user data for destructive tests.

---

# 🗺️ Roadmap

## Phase 1 — Foundation

* [ ] Repository
* [ ] Windows desktop UI
* [ ] Local database
* [ ] Configuration
* [ ] Basic local model
* [ ] Chat Mode

## Phase 2 — AI Core

* [ ] Model Gateway
* [ ] Model Registry
* [ ] External API Providers
* [ ] Model Router
* [ ] Context Management

## Phase 3 — Memory & RAG

* [ ] Conversation Memory
* [ ] User Memory
* [ ] Project Memory
* [ ] Vector Storage
* [ ] File Ingestion
* [ ] Local RAG

## Phase 4 — Windows Tools

* [ ] Filesystem
* [ ] Terminal
* [ ] PowerShell
* [ ] CMD
* [ ] Application Manager
* [ ] Process Manager
* [ ] Screenshot System

## Phase 5 — Permissions

* [ ] Safe Mode
* [ ] Autonomous Mode
* [ ] Risk Mode
* [ ] Permission Engine
* [ ] Risk Classification
* [ ] Audit Logs
* [ ] Emergency STOP

## Phase 6 — KritiMode

* [ ] Goal Engine
* [ ] Planner
* [ ] Task Engine
* [ ] Agent Manager
* [ ] Execution Loop
* [ ] Pause/Resume
* [ ] Verification

## Phase 7 — Windows Agent

* [ ] UI Automation
* [ ] Keyboard
* [ ] Mouse
* [ ] Clipboard
* [ ] Application Control
* [ ] Process Control

## Phase 8 — Browser & Vision

* [ ] Browser Agent
* [ ] DOM
* [ ] Accessibility
* [ ] Vision
* [ ] Screenshot Understanding
* [ ] Browser Verification

## Phase 9 — Developer Agent

* [ ] Coding Agent
* [ ] Testing Agent
* [ ] Debugging Agent
* [ ] Git Agent
* [ ] GitHub Agent
* [ ] Docker
* [ ] Deployment

## Phase 10 — Autonomous Execution

* [ ] Self-Correction
* [ ] Recovery
* [ ] Re-planning
* [ ] Long-running Tasks
* [ ] Background Execution
* [ ] Advanced Verification

## Phase 11 — Automation

* [ ] Scheduler
* [ ] Recurring Tasks
* [ ] Notifications
* [ ] Background Workflows

## Phase 12 — Updates

* [ ] GitHub Releases
* [ ] Update Detection
* [ ] Installer
* [ ] Integrity Verification
* [ ] Rollback

## Phase 13 — Plugins

* [ ] Plugin SDK
* [ ] Tool Plugins
* [ ] Agent Plugins
* [ ] Model Plugins
* [ ] Integration Plugins
* [ ] Plugin Permissions

---

# 🧱 Development Philosophy

KritiAI should be developed incrementally.

For every feature:

```text
Design
 ↓
Implement
 ↓
Test
 ↓
Debug
 ↓
Verify
 ↓
Document
 ↓
Release
```

Never pretend a feature is implemented when it is only a placeholder.

Use:

```text
Planned
```

for features that have not been implemented.

Use:

```text
Experimental
```

for incomplete or unstable features.

Use:

```text
Stable
```

only after appropriate testing.

---

# 👥 Team

### Developers

* Infinity Coding
* Project Collaborator

---

# 🤝 Contributing

Contributions are welcome.

Before contributing:

1. Read the documentation.
2. Understand the architecture.
3. Follow the security principles.
4. Add tests.
5. Keep changes focused.
6. Update documentation.
7. Do not commit secrets.

---

# 📄 License

KritiAI is intended to be open source.

The final open-source license will be selected before public release.

---

# 🎯 Long-Term Goal

KritiAI aims to evolve from:

```text
AI CHATBOT
      ↓
AI ASSISTANT
      ↓
AI AGENT
      ↓
AI EXECUTION PLATFORM
      ↓
PERSONAL AI OPERATING LAYER FOR WINDOWS
```

The ultimate goal is to allow a user to express an outcome instead of manually describing every action.

For example:

```text
"Play Sita Ram."
```

```text
"Create a website for my project."
```

```text
"Fix the errors in my application."
```

```text
"Research this topic and create a report."
```

```text
"Create the project, test it, commit it,
and push it to GitHub."
```

KritiAI should understand the goal, determine the required steps, select the appropriate model and tools, execute the workflow, verify the results, recover from failures, and report what happened.

---

# 🤖 KRITIAI

> **Your Personal AI Assistant & Execution Layer**

```text
YOUR IDEA
    ↓
KRITIAI
    ↓
UNDERSTAND
    ↓
PLAN
    ↓
EXECUTE
    ↓
OBSERVE
    ↓
VERIFY
    ↓
RECOVER
    ↓
COMPLETE
```

**From an idea to execution — KritiAI helps you do it.**
