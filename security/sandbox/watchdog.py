"""Emergency Stop and Process Watchdog for KritiAI."""
import os
import signal
import threading
from typing import Any, Dict, List, Optional, Set
import psutil

from config.settings import get_config


class EmergencyStopManager:
    """Global Emergency STOP controller and process supervisor."""
    _instance: Optional["EmergencyStopManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EmergencyStopManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EmergencyStopManager, cls).__new__(cls)
                cls._instance._is_stopped = False
                cls._instance._tracked_pids: Set[int] = set()
                cls._active_task_ids: Set[str] = set()
            return cls._instance

    @property
    def is_stopped(self) -> bool:
        return self._is_stopped

    def register_pid(self, pid: int) -> None:
        """Register a subprocess PID spawned by KritiAI."""
        if self._is_stopped:
            # Terminate immediately if stop is active
            self._kill_pid(pid)
            return
        self._tracked_pids.add(pid)

    def unregister_pid(self, pid: int) -> None:
        self._tracked_pids.discard(pid)

    def register_task(self, task_id: str) -> None:
        self._active_task_ids.add(task_id)

    def unregister_task(self, task_id: str) -> None:
        self._active_task_ids.discard(task_id)

    def trigger_emergency_stop(self, reason: str = "User activated Emergency STOP") -> Dict[str, Any]:
        """Immediately halt task scheduling and terminate all active child processes."""
        with self._lock:
            self._is_stopped = True
            killed_pids: List[int] = []
            
            for pid in list(self._tracked_pids):
                if self._kill_pid(pid):
                    killed_pids.append(pid)
                self._tracked_pids.discard(pid)

            # Update application configuration state
            config = get_config()
            config.emergency_stop_active = True

            return {
                "status": "STOPPED",
                "reason": reason,
                "terminated_pids": killed_pids,
                "interrupted_tasks": list(self._active_task_ids)
            }

    def reset_emergency_stop(self) -> None:
        """Reset emergency stop state after user verification."""
        with self._lock:
            self._is_stopped = False
            config = get_config()
            config.emergency_stop_active = False

    def _kill_pid(self, pid: int) -> bool:
        """Terminate a process and all its child processes cleanly."""
        try:
            if not psutil.pid_exists(pid):
                return False
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            parent.terminate()
            # Wait briefly, then force kill if still alive
            _, still_alive = psutil.wait_procs(children + [parent], timeout=2)
            for p in still_alive:
                try:
                    p.kill()
                except Exception:
                    pass
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        except Exception:
            return False


# Global singleton helper
def get_emergency_stop_manager() -> EmergencyStopManager:
    return EmergencyStopManager()
