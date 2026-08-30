import os
import subprocess
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai.gateway.gateway import ModelGateway
from ai.router.router import ModelRouter
from config.settings import AppConfig, PowerMode, get_config, save_config
from core.orchestrator.orchestrator import AIOrchestrator
from core.task_engine.engine import TaskEngine
from database.repository import Repository
from memory.manager import MemoryManager
from security.audit.logger import AuditLogger
from security.sandbox.watchdog import get_emergency_stop_manager
from tools.registry import ToolRegistry
from tools.windows.system_info import SystemInfoTool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("kritiai.desktop")

app = FastAPI(title="KritiAI Desktop API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared singletons
config = get_config()
repo = Repository()
audit_logger = AuditLogger(repo)
tool_registry = ToolRegistry(config, audit_logger=audit_logger)
memory_mgr = MemoryManager(repo)
model_gateway = ModelGateway(config)
model_router = ModelRouter(model_gateway, config)
task_engine = TaskEngine(repo)
orchestrator = AIOrchestrator(
    config=config,
    task_engine=task_engine,
    tool_registry=tool_registry,
    memory_manager=memory_mgr,
    model_gateway=model_gateway,
    model_router=model_router
)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()


# Schemas
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    mode: str = "chat"
    model: Optional[str] = None


class ConfigureProviderRequest(BaseModel):
    provider: str = "openai_compatible"
    api_key: Optional[str] = ""
    base_url: Optional[str] = "https://api.openai.com/v1"
    default_model: Optional[str] = "gpt-4o"


class ExecuteGoalRequest(BaseModel):
    goal: str
    session_id: Optional[str] = None
    power_mode: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    power_mode: Optional[str] = None
    general_model: Optional[str] = None
    coding_model: Optional[str] = None
    prefer_local: Optional[bool] = None
    allow_filesystem: Optional[bool] = None
    allow_terminal: Optional[bool] = None
    allow_powershell: Optional[bool] = None
    allow_application_control: Optional[bool] = None
    allow_keyboard_mouse: Optional[bool] = None


# Endpoints
@app.get("/api/config")
def get_current_config() -> Dict[str, Any]:
    cfg = get_config()
    stop_mgr = get_emergency_stop_manager()
    return {
        "app_name": cfg.app_name,
        "version": cfg.version,
        "power_mode": cfg.power_mode.value,
        "emergency_stop_active": stop_mgr.is_stopped,
        "permissions": cfg.permissions.model_dump(),
        "models": cfg.models.model_dump(),
        "privacy": cfg.privacy.model_dump(),
        "workspace_dir": str(cfg.workspace_dir)
    }


@app.post("/api/config")
def update_configuration(req: ConfigUpdateRequest) -> Dict[str, Any]:
    cfg = get_config()
    if req.power_mode:
        cfg.power_mode = PowerMode(req.power_mode)
    if req.general_model is not None:
        cfg.models.general_model = req.general_model
    if req.coding_model is not None:
        cfg.models.coding_model = req.coding_model
    if req.prefer_local is not None:
        cfg.models.prefer_local = req.prefer_local
    if req.allow_filesystem is not None:
        cfg.permissions.allow_filesystem = req.allow_filesystem
    if req.allow_terminal is not None:
        cfg.permissions.allow_terminal = req.allow_terminal
    if req.allow_powershell is not None:
        cfg.permissions.allow_powershell = req.allow_powershell
    if req.allow_application_control is not None:
        cfg.permissions.allow_application_control = req.allow_application_control
    if req.allow_keyboard_mouse is not None:
        cfg.permissions.allow_keyboard_mouse = req.allow_keyboard_mouse
    save_config(cfg)
    model_router.config = cfg
    return {"status": "success", "config": get_current_config()}


@app.post("/api/emergency-stop")
async def trigger_emergency_stop() -> Dict[str, Any]:
    stop_mgr = get_emergency_stop_manager()
    result = stop_mgr.trigger_emergency_stop(reason="User clicked Emergency STOP button")
    await ws_manager.broadcast({"event": "emergency_stop", "data": result})
    return result


@app.post("/api/emergency-stop/reset")
async def reset_emergency_stop() -> Dict[str, Any]:
    stop_mgr = get_emergency_stop_manager()
    stop_mgr.reset_emergency_stop()
    await ws_manager.broadcast({"event": "emergency_stop_reset"})
    return {"status": "RESET", "emergency_stop_active": False}


@app.get("/api/models")
def get_all_models() -> Dict[str, Any]:
    """Retrieve all discovered local models and integrated external API models."""
    models = model_gateway.list_all_models()

    # Priority for default chat model: Qwen 7B
    default_chat_model = None
    for m in models:
        mid = m["id"].lower()
        if "qwen" in mid and ("7b" in mid or "2.5" in mid):
            default_chat_model = m["id"]
            break

    if not default_chat_model:
        for m in models:
            if "qwen" in m["id"].lower():
                default_chat_model = m["id"]
                break

    if not default_chat_model:
        default_chat_model = "ollama:qwen2.5:7b" if "ollama" in model_gateway._providers else (models[0]["id"] if models else "offline_local:qwen2.5:7b-emulated")

    active_model = default_chat_model
    return {
        "active_model": active_model,
        "default_chat_model": default_chat_model,
        "models": models,
        "providers": {
            p_name: {"available": p.is_available()}
            for p_name, p in model_gateway._providers.items()
        }
    }


@app.post("/api/models/providers")
def configure_api_provider(req: ConfigureProviderRequest) -> Dict[str, Any]:
    """Configure external API provider credentials and dynamically discover models."""
    config.models.openai_api_key = req.api_key or ""
    config.models.openai_base_url = req.base_url or "https://api.openai.com/v1"
    config.models.openai_model = req.default_model or "gpt-4o"
    config.save()
    model_gateway.refresh_providers(config)
    discovered = model_gateway.list_all_models()
    return {
        "success": True,
        "models": discovered,
        "message": f"Provider configured. Found {len(discovered)} available model(s)."
    }


@app.post("/api/chat")
def handle_chat(req: ChatRequest) -> Dict[str, Any]:
    session_id = req.session_id
    if not session_id:
        sess = repo.create_session(title=req.message[:30], mode=req.mode)
        session_id = sess["id"]

    # Record user message
    repo.add_message(session_id=session_id, role="user", content=req.message)

    # Check if this is a Current Affairs & Latest Topics question
    is_current_affairs = ModelRouter.is_current_affairs_query(req.message)
    switched_model = False
    switch_reason = None

    if is_current_affairs:
        # Dynamically switch model to Qwen or DeepSeek
        prov_name, model_name = model_router.route_current_affairs(req.message)
        switched_model = True
        switch_reason = f"Auto-routed to {model_name} for Current Affairs & Latest Topics"
    elif req.model:
        prov_name = None
        model_name = req.model
    else:
        # Default for chat only is Qwen 7B
        prov_name, model_name = model_router.route_chat_default()

    history = repo.get_messages(session_id)
    chat_messages = [{"role": m["role"], "content": m["content"]} for m in history]

    model_resp = model_gateway.generate(messages=chat_messages, provider_name=prov_name, model=model_name)

    actual_model = f"{model_name}" if model_name else f"{prov_name}/{model_resp.model}"

    # Record assistant message
    repo.add_message(
        session_id=session_id,
        role="assistant",
        content=model_resp.content,
        model=actual_model,
        tool_calls=model_resp.tool_calls
    )

    return {
        "session_id": session_id,
        "content": model_resp.content,
        "model": actual_model,
        "switched_model": switched_model,
        "switch_reason": switch_reason,
        "tool_calls": model_resp.tool_calls,
        "latency_ms": model_resp.latency_ms
    }


@app.post("/api/kritimode/execute")
async def execute_goal(req: ExecuteGoalRequest) -> Dict[str, Any]:
    loop = asyncio.get_event_loop()

    def step_cb(payload: Dict[str, Any]) -> None:
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(payload), loop)

    power = PowerMode(req.power_mode) if req.power_mode else config.power_mode
    # Run synchronously in thread pool to not block event loop
    result = await asyncio.to_thread(
        orchestrator.run_goal,
        goal=req.goal,
        session_id=req.session_id,
        power_mode=power,
        step_callback=step_cb
    )
    return result


@app.get("/api/tasks")
def list_tasks() -> List[Dict[str, Any]]:
    return repo.list_tasks(limit=50)


@app.get("/api/tasks/{task_id}")
def get_task_details(task_id: str) -> Dict[str, Any]:
    t = repo.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t["steps"] = repo.get_task_steps(task_id)
    return t


@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str) -> Dict[str, Any]:
    res = task_engine.pause_task(task_id)
    await ws_manager.broadcast({"event": "task_paused", "task_id": task_id})
    return res


@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str) -> Dict[str, Any]:
    res = task_engine.resume_task(task_id)
    await ws_manager.broadcast({"event": "task_resumed", "task_id": task_id})
    return res


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> Dict[str, Any]:
    res = task_engine.cancel_task(task_id)
    await ws_manager.broadcast({"event": "task_cancelled", "task_id": task_id})
    return res


class ApproveTaskRequest(BaseModel):
    decision: str = "allow_once"  # allow_once, always_allow, deny
    tool_name: Optional[str] = None
    action: Optional[str] = None
    modified_plan_markdown: Optional[str] = None


@app.post("/api/tasks/{task_id}/approve")
async def approve_task_step(task_id: str, req: ApproveTaskRequest) -> Dict[str, Any]:
    """Resume execution of a task after user interaction with the Approval Modal or Plan Editor."""
    loop = asyncio.get_event_loop()

    def step_cb(payload: Dict[str, Any]) -> None:
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(payload), loop)

    result = await asyncio.to_thread(
        orchestrator.resume_task_after_approval,
        task_id=task_id,
        decision=req.decision,
        modified_plan_markdown=req.modified_plan_markdown,
        step_callback=step_cb
    )
    return result


class OpenPathRequest(BaseModel):
    path: str


@app.post("/api/open-path")
def open_path(req: OpenPathRequest) -> Dict[str, Any]:
    import os
    import subprocess
    import webbrowser

    raw_path = (req.path or "").strip()
    if not raw_path:
        return {"success": False, "error": "Empty path provided"}

    # Handle Web URLs
    if raw_path.startswith("http://") or raw_path.startswith("https://"):
        try:
            if os.name == "nt":
                os.startfile(raw_path)
            else:
                webbrowser.open_new(raw_path)
            return {"success": True, "path": raw_path}
        except Exception as ex:
            return {"success": False, "error": str(ex)}

    # Strip file:/// URI scheme if present
    if raw_path.startswith("file:///"):
        raw_path = raw_path[8:]
    elif raw_path.startswith("file://"):
        raw_path = raw_path[7:]

    clean_path = raw_path.strip("\"'")
    clean_path = os.path.normpath(clean_path)
    target = os.path.abspath(clean_path)

    # If target doesn't exist, check parent folder
    if not os.path.exists(target):
        parent = os.path.dirname(target)
        if os.path.exists(parent):
            target = parent
        else:
            return {"success": False, "error": f"Path '{target}' does not exist on filesystem."}

    try:
        if os.name == "nt":
            if os.path.isdir(target):
                subprocess.Popen(["explorer.exe", target])
            elif os.path.isfile(target):
                subprocess.Popen(["explorer.exe", f"/select,{target}"])
            else:
                subprocess.Popen(["explorer.exe", target])
        else:
            subprocess.Popen(["xdg-open", target])
        return {"success": True, "path": target}
    except Exception as ex:
        return {"success": False, "error": str(ex)}


class NativePickRequest(BaseModel):
    pick_type: str = "folder"  # "folder" or "file"
    initial_dir: Optional[str] = None


@app.get("/api/fs/drives")
def get_filesystem_drives() -> List[str]:
    """Get list of active Windows drive roots."""
    import string
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(drive_path)
    return drives or ["C:\\"]


@app.get("/api/fs/browse")
def browse_filesystem(path: Optional[str] = None) -> Dict[str, Any]:
    """List folders and files in a directory for the in-app file explorer modal."""
    if not path or not os.path.exists(path):
        path = os.getcwd()

    norm_path = os.path.normpath(path)
    if os.path.isfile(norm_path):
        norm_path = os.path.dirname(norm_path)

    parent_path = os.path.dirname(norm_path) if os.path.dirname(norm_path) != norm_path else None

    folders = []
    files = []

    try:
        with os.scandir(norm_path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name.startswith(".") and entry.name not in [".github"]:
                            continue
                        folders.append({
                            "name": entry.name,
                            "path": entry.path,
                            "is_dir": True,
                            "modified_time": os.path.getmtime(entry.path)
                        })
                    elif entry.is_file(follow_symlinks=False):
                        files.append({
                            "name": entry.name,
                            "path": entry.path,
                            "is_dir": False,
                            "size_bytes": entry.stat().st_size,
                            "modified_time": entry.stat().st_mtime
                        })
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError) as err:
        return {
            "success": False,
            "error": f"Cannot access path: {err}",
            "current_path": norm_path,
            "parent_path": parent_path,
            "folders": [],
            "files": []
        }

    folders.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())

    return {
        "success": True,
        "current_path": norm_path,
        "parent_path": parent_path,
        "folders": folders,
        "files": files
    }


@app.post("/api/fs/native_pick")
def native_pick_dialog(req: NativePickRequest) -> Dict[str, Any]:
    """Launch native Windows file/folder picker dialog via PowerShell STA."""
    init_dir = req.initial_dir or os.getcwd()
    if not os.path.exists(init_dir):
        init_dir = "C:\\"

    if req.pick_type == "file":
        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.OpenFileDialog
$f.InitialDirectory = '{init_dir.replace("'", "''")}'
$f.Title = 'Select Project File'
$res = $f.ShowDialog()
if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $f.FileName
}}
"""
    else:
        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.FolderBrowserDialog
$f.SelectedPath = '{init_dir.replace("'", "''")}'
$f.Description = 'Select Project Workspace Directory'
$f.ShowNewFolderButton = $true
$res = $f.ShowDialog()
if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $f.SelectedPath
}}
"""
    try:
        res = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Sta", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=60
        )
        selected_path = res.stdout.strip()
        if selected_path and os.path.exists(selected_path):
            return {"success": True, "path": selected_path, "is_file": os.path.isfile(selected_path)}
        return {"success": False, "cancelled": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


class SupervisionInspectRequest(BaseModel):
    path: str


class SupervisionModifyRequest(BaseModel):
    path: str
    instruction: str
    model: Optional[str] = None


@app.post("/api/supervision/inspect")
def supervision_inspect(req: SupervisionInspectRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.inspect_project(req.path)


@app.post("/api/supervision/modify")
def supervision_modify(req: SupervisionModifyRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.apply_senior_developer_changes(
        raw_path=req.path,
        instruction=req.instruction,
        model_gateway=model_gateway,
        model_router=model_router
    )


class SupervisionFileWriteRequest(BaseModel):
    path: str
    file: str
    content: str
    author: Optional[str] = "user"
    reason: Optional[str] = ""
    expected_base_hash: Optional[str] = None


class SupervisionPlanSaveRequest(BaseModel):
    path: str
    markdown: str


class TerminalRunRequest(BaseModel):
    path: str
    command: str


class SupervisionUndoRequest(BaseModel):
    path: str


class SupervisionRedoRequest(BaseModel):
    path: str


class SupervisionUndoGroupRequest(BaseModel):
    path: str
    group_id: str


class SupervisionSnapshotCreateRequest(BaseModel):
    path: str
    title: str


class SupervisionSnapshotRestoreRequest(BaseModel):
    path: str
    snapshot_id: str


class SupervisionFileCreateRequest(BaseModel):
    path: str
    file: str
    content: Optional[str] = ""
    author: Optional[str] = "user"


class SupervisionFileDeleteRequest(BaseModel):
    path: str
    file: str
    author: Optional[str] = "user"


class SupervisionFileRenameRequest(BaseModel):
    path: str
    old_path: str
    new_path: str
    author: Optional[str] = "user"


class SupervisionFolderCreateRequest(BaseModel):
    path: str
    folder: str


class SupervisionFolderDeleteRequest(BaseModel):
    path: str
    folder: str


class SupervisionFormatRequest(BaseModel):
    path: str
    file: str


class SupervisionConflictCheckRequest(BaseModel):
    path: str
    file: str
    expected_hash: Optional[str] = None


class SupervisionChangeDecideRequest(BaseModel):
    path: str
    group_id: str
    decision: str  # "accept" | "reject"


@app.get("/api/supervision/file")
def supervision_read_file(path: str, file: str) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.read_file(path, file)


@app.post("/api/supervision/file")
def supervision_write_file(req: SupervisionFileWriteRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.write_file(
        project_dir=req.path,
        rel_path=req.file,
        new_content=req.content,
        author=req.author or "user",
        reason=req.reason or "",
        expected_base_hash=req.expected_base_hash
    )


@app.get("/api/supervision/git")
def supervision_get_git(path: str) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.get_git_state(path)


@app.post("/api/supervision/plan/save")
def supervision_save_plan(req: SupervisionPlanSaveRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.write_file(req.path, "IMPLEMENTATION_PLAN.md", req.markdown)


@app.post("/api/terminal/run")
def terminal_run(req: TerminalRunRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.run_command(req.path, req.command)


# =========================================================================
# COLLABORATIVE HISTORY, UNDO/REDO & SNAPSHOT ENDPOINTS
# =========================================================================

@app.get("/api/supervision/history")
def supervision_get_history(path: str) -> List[Dict[str, Any]]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.get_history(path)


@app.get("/api/supervision/history/{change_id}")
def supervision_get_change_detail(change_id: str, path: str) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    res = SupervisionEngine.get_change_detail(path, change_id)
    return res or {"error": "Change not found"}


@app.get("/api/supervision/group/{group_id}")
def supervision_get_group_detail(group_id: str, path: str) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    res = SupervisionEngine.get_group_detail(path, group_id)
    return res or {"error": "Group not found"}


@app.post("/api/supervision/undo")
def supervision_undo(req: SupervisionUndoRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.undo(req.path)


@app.post("/api/supervision/redo")
def supervision_redo(req: SupervisionRedoRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.redo(req.path)


@app.post("/api/supervision/undo/group")
def supervision_undo_group(req: SupervisionUndoGroupRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.undo_group(req.path, req.group_id)


@app.get("/api/supervision/snapshots")
def supervision_list_snapshots(path: str) -> List[Dict[str, Any]]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.list_snapshots(path)


@app.post("/api/supervision/snapshots")
def supervision_create_snapshot(req: SupervisionSnapshotCreateRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.create_snapshot(req.path, req.title)


@app.post("/api/supervision/snapshots/restore")
def supervision_restore_snapshot(req: SupervisionSnapshotRestoreRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.restore_snapshot(req.path, req.snapshot_id)


@app.post("/api/supervision/file/create")
def supervision_create_file(req: SupervisionFileCreateRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.create_file(req.path, req.file, req.content or "", author=req.author or "user")


@app.post("/api/supervision/file/delete")
def supervision_delete_file(req: SupervisionFileDeleteRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.delete_file(req.path, req.file, author=req.author or "user")


@app.post("/api/supervision/file/rename")
def supervision_rename_file(req: SupervisionFileRenameRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.rename_file(req.path, req.old_path, req.new_path, author=req.author or "user")


@app.post("/api/supervision/folder/create")
def supervision_create_folder(req: SupervisionFolderCreateRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.create_folder(req.path, req.folder)


@app.post("/api/supervision/folder/delete")
def supervision_delete_folder(req: SupervisionFolderDeleteRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.delete_folder(req.path, req.folder)


@app.post("/api/supervision/format")
def supervision_format_code(req: SupervisionFormatRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.format_code(req.path, req.file)


@app.post("/api/supervision/conflict/check")
def supervision_check_conflict(req: SupervisionConflictCheckRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    return SupervisionEngine.check_conflict(req.path, req.file, req.expected_hash)


@app.post("/api/supervision/changes/decide")
def supervision_decide_changes(req: SupervisionChangeDecideRequest) -> Dict[str, Any]:
    from core.supervision.engine import SupervisionEngine
    if req.decision.lower() == "reject":
        return SupervisionEngine.undo_group(req.path, req.group_id)
    return {
        "success": True,
        "group_id": req.group_id,
        "status": "accepted",
        "message": "AI changes accepted by user."
    }


@app.get("/api/audit")
def list_audit_logs(task_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo.get_audit_logs(task_id=task_id, limit=100)


@app.get("/api/memory")
def list_memory_entries() -> List[Dict[str, Any]]:
    return memory_mgr.list_memories()


@app.delete("/api/memory")
def clear_memories() -> Dict[str, Any]:
    cleared = memory_mgr.clear()
    return {"cleared_count": cleared}


@app.get("/api/system-info")
def get_system_hardware() -> Dict[str, Any]:
    sys_tool = SystemInfoTool()
    res = sys_tool.execute()
    return res.data or {}


@app.get("/api/tools")
def get_registered_tools() -> List[Dict[str, Any]]:
    return tool_registry.list_tools()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming ping or messages
            await websocket.send_json({"event": "pong", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# Static assets
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def serve_index() -> FileResponse:
        return FileResponse(str(static_dir / "index.html"))
