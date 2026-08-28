"""Standardized Windows Command Execution Runner."""
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil

from security.sandbox.watchdog import get_emergency_stop_manager


class CommandRunner:
    """Executes commands on Windows via PowerShell or CMD with safety watchdogs."""

    @staticmethod
    def execute(
        command: str,
        shell: str = "powershell",
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        timeout: int = 60,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        stop_mgr = get_emergency_stop_manager()
        if stop_mgr.is_stopped:
            return {
                "command": command,
                "shell": shell,
                "working_directory": working_directory or os.getcwd(),
                "exit_code": -1,
                "stdout": "",
                "stderr": "Execution cancelled: Emergency STOP is active.",
                "duration": 0.0,
                "timed_out": False,
                "status": "CANCELLED",
                "pid": None
            }

        # Resolve working directory
        cwd = working_directory or os.getcwd()
        if not os.path.isdir(cwd):
            try:
                os.makedirs(cwd, exist_ok=True)
            except Exception as ex:
                return {
                    "command": command,
                    "shell": shell,
                    "working_directory": cwd,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Failed to create/access working directory '{cwd}': {str(ex)}",
                    "duration": 0.0,
                    "timed_out": False,
                    "status": "FAILED",
                    "pid": None
                }

        # Prepare environment
        env = os.environ.copy()
        if environment:
            env.update(environment)

        # Build command invocation
        if shell.lower() == "powershell":
            # Use PowerShell with execution policy bypass for script running
            args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command]
        elif shell.lower() == "cmd":
            args = ["cmd.exe", "/c", command]
        else:
            args = [shell, command]

        start_time = time.time()
        timed_out = False
        pid = None

        try:
            proc = subprocess.Popen(
                args,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            pid = proc.pid
            stop_mgr.register_pid(pid)

            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                # Kill process and all children
                try:
                    p = psutil.Process(proc.pid)
                    for child in p.children(recursive=True):
                        child.kill()
                    p.kill()
                except Exception:
                    proc.kill()
                stdout, stderr = proc.communicate()
                exit_code = -1
            finally:
                stop_mgr.unregister_pid(pid)

            duration = round(time.time() - start_time, 3)

            if timed_out:
                status = "TIMEOUT"
            elif stop_mgr.is_stopped:
                status = "CANCELLED"
            elif exit_code == 0:
                status = "SUCCESS"
            else:
                status = "FAILED"

            return {
                "command": command,
                "shell": shell,
                "working_directory": cwd,
                "exit_code": exit_code,
                "stdout": stdout or "",
                "stderr": stderr or "",
                "duration": duration,
                "timed_out": timed_out,
                "status": status,
                "pid": pid
            }

        except Exception as ex:
            duration = round(time.time() - start_time, 3)
            return {
                "command": command,
                "shell": shell,
                "working_directory": cwd,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Subprocess launch error: {str(ex)}",
                "duration": duration,
                "timed_out": False,
                "status": "FAILED",
                "pid": pid
            }
