"""FastAPI Backend Server and WebSocket Hub for KritiAI Windows Desktop."""
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


@app.post("/api/chat")
def handle_chat(req: ChatRequest) -> Dict[str, Any]:
    session_id = req.session_id
    if not session_id:
        sess = repo.create_session(title=req.message[:30], mode=req.mode)
        session_id = sess["id"]

    # Record user message
    repo.add_message(session_id=session_id, role="user", content=req.message)

    # Route and generate response via ModelGateway
    prov_name, model_name = model_router.route(task_type="general")
    history = repo.get_messages(session_id)
    chat_messages = [{"role": m["role"], "content": m["content"]} for m in history]

    model_resp = model_gateway.generate(messages=chat_messages, provider_name=prov_name, model=model_name)

    # Record assistant message
    repo.add_message(
        session_id=session_id,
        role="assistant",
        content=model_resp.content,
        model=f"{prov_name}/{model_name}",
        tool_calls=model_resp.tool_calls
    )

    return {
        "session_id": session_id,
        "content": model_resp.content,
        "model": f"{prov_name}/{model_name}",
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
