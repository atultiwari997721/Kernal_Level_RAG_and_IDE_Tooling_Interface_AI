"""Database Repository for KritiAI entities."""
from datetime import datetime
import json
from typing import Any, Dict, List, Optional
import uuid

from database.connection import DatabaseConnection


class Repository:
    """CRUD operations for tasks, sessions, memory, and audit logs."""

    def __init__(self, db: Optional[DatabaseConnection] = None):
        self.db = db or DatabaseConnection()

    # --- Sessions & Messages ---
    def create_session(self, title: str = "New Session", mode: str = "chat") -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, mode, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, mode, title, now, now)
            )
        return {"id": session_id, "mode": mode, "title": title, "created_at": now, "updated_at": now}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            return dict(row) if row else None

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def add_message(
        self, session_id: str, role: str, content: str, model: Optional[str] = None, tool_calls: Optional[Any] = None
    ) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (id, session_id, role, content, model, tool_calls, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, model, tool_calls_json, now)
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        return {
            "id": msg_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "model": model,
            "tool_calls": tool_calls,
            "created_at": now
        }

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,)
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if d.get("tool_calls"):
                    try:
                        d["tool_calls"] = json.loads(d["tool_calls"])
                    except Exception:
                        pass
                result.append(d)
            return result

    # --- Tasks ---
    def create_task(
        self,
        goal: str,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        mode: str = "kritimode",
        power_mode: str = "autonomous"
    ) -> Dict[str, Any]:
        t_id = task_id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT INTO tasks (
                    id, session_id, goal, mode, power_mode, status, current_step,
                    active_agent, active_model, active_tool, observations, errors,
                    retries, verification_status, final_result, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'created', 0, NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, ?, ?)""",
                (t_id, session_id, goal, mode, power_mode, now, now)
            )
        return self.get_task(t_id)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            if data.get("plan_json"):
                try:
                    data["plan"] = json.loads(data["plan_json"])
                except Exception:
                    data["plan"] = []
            else:
                data["plan"] = []
            return data

    def update_task(self, task_id: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow().isoformat()
        kwargs["updated_at"] = now
        if "plan" in kwargs:
            kwargs["plan_json"] = json.dumps(kwargs.pop("plan"))
        
        clauses = [f"{k} = ?" for k in kwargs.keys()]
        values = list(kwargs.values()) + [task_id]
        
        with self.db.get_connection() as conn:
            conn.execute(f"UPDATE tasks SET {', '.join(clauses)} WHERE id = ?", values)
        return self.get_task(task_id)

    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if d.get("plan_json"):
                    try:
                        d["plan"] = json.loads(d["plan_json"])
                    except Exception:
                        d["plan"] = []
                result.append(d)
            return result

    # --- Task Steps ---
    def save_task_steps(self, task_id: str, steps: List[Dict[str, Any]]) -> None:
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM task_steps WHERE task_id = ?", (task_id,))
            for i, step in enumerate(steps):
                step_id = step.get("id") or str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO task_steps (
                        id, task_id, step_index, objective, agent, tool, input_data,
                        output_data, expected_result, verification_condition, status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        step_id,
                        task_id,
                        i,
                        step.get("objective", ""),
                        step.get("agent", ""),
                        step.get("tool", ""),
                        json.dumps(step.get("input_data", {})),
                        json.dumps(step.get("output_data", {})),
                        step.get("expected_result", ""),
                        step.get("verification_condition", ""),
                        step.get("status", "pending"),
                        step.get("error_message")
                    )
                )

    def get_task_steps(self, task_id: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM task_steps WHERE task_id = ? ORDER BY step_index ASC", (task_id,)
            ).fetchall()
            steps = []
            for r in rows:
                d = dict(r)
                if d.get("input_data"):
                    try:
                        d["input_data"] = json.loads(d["input_data"])
                    except Exception:
                        pass
                if d.get("output_data"):
                    try:
                        d["output_data"] = json.loads(d["output_data"])
                    except Exception:
                        pass
                steps.append(d)
            return steps

    # --- Memory ---
    def add_memory(
        self, tier: str, content: str, key: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        mem_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata) if metadata else None
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO memory_entries (id, tier, key, content, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (mem_id, tier, key, content, meta_json, now, now)
            )
        return {"id": mem_id, "tier": tier, "key": key, "content": content, "metadata": metadata, "created_at": now}

    def get_memories(self, tier: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            if tier:
                rows = conn.execute(
                    "SELECT * FROM memory_entries WHERE tier = ? ORDER BY updated_at DESC LIMIT ?", (tier, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memory_entries ORDER BY updated_at DESC LIMIT ?", (limit,)
                ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if d.get("metadata"):
                    try:
                        d["metadata"] = json.loads(d["metadata"])
                    except Exception:
                        pass
                result.append(d)
            return result

    def delete_memory(self, memory_id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM memory_entries WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def clear_memory(self, tier: Optional[str] = None) -> int:
        with self.db.get_connection() as conn:
            if tier:
                cursor = conn.execute("DELETE FROM memory_entries WHERE tier = ?", (tier,))
            else:
                cursor = conn.execute("DELETE FROM memory_entries")
            return cursor.rowcount

    # --- Audit Logs ---
    def log_audit(
        self,
        tool: str,
        action: str,
        risk_level: str,
        power_mode: str,
        decision: str,
        status: str,
        task_id: Optional[str] = None,
        agent: Optional[str] = None,
        details: Optional[str] = None,
        verification_result: Optional[str] = None
    ) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO audit_logs (
                    task_id, agent, tool, action, risk_level, power_mode,
                    decision, status, details, verification_result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (task_id, agent, tool, action, risk_level, power_mode, decision, status, details, verification_result)
            )
            return cursor.lastrowid

    def get_audit_logs(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            if task_id:
                rows = conn.execute(
                    "SELECT * FROM audit_logs WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?", (task_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]
