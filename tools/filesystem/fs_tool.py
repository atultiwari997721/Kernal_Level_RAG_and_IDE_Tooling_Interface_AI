"""Standardized Windows Filesystem Tool for KritiAI."""
import os
import shutil
import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult


class FilesystemTool(BaseTool):
    """Safe, verifiable Windows filesystem tool."""
    name = "filesystem"
    description = "Manage files and directories on Windows: create, read, write, edit, delete, copy, move, list, search."
    input_schema = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["create_file", "create_folder", "read_file", "write_file", "edit_file", "delete", "copy", "move", "rename", "list_dir", "search"]
            },
            "path": {"type": "string", "description": "Target file or directory path"},
            "destination": {"type": "string", "description": "Destination path for copy/move/rename", "optional": True},
            "content": {"type": "string", "description": "Text content to write or search", "optional": True},
            "pattern": {"type": "string", "description": "Search pattern (glob or string)", "optional": True},
        },
        "required": ["operation", "path"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string"},
            "path": {"type": "string"},
            "result": {"type": "any"},
            "verified": {"type": "boolean"},
        }
    }
    risk_level = RiskLevel.MEDIUM
    required_permission = "allow_filesystem"
    timeout_seconds = 30

    def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation", "").lower()
        path_str = kwargs.get("path", "")
        dest_str = kwargs.get("destination")
        content = kwargs.get("content", "")
        pattern = kwargs.get("pattern", "*")

        # Map risk level according to operation
        if operation in ["delete"]:
            self.risk_level = RiskLevel.HIGH
        elif operation in ["read_file", "list_dir", "search"]:
            self.risk_level = RiskLevel.LOW
        else:
            self.risk_level = RiskLevel.MEDIUM

        target = Path(path_str).resolve()
        
        try:
            if operation == "create_folder":
                target.mkdir(parents=True, exist_ok=True)
                res_data = {"created_dir": str(target)}

            elif operation == "create_file" or operation == "write_file":
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
                res_data = {"written_bytes": len(content.encode("utf-8")), "file": str(target)}

            elif operation == "read_file":
                if not target.is_file():
                    return ToolResult(success=False, error=f"File '{target}' not found.")
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    file_content = f.read()
                res_data = {"content": file_content, "size_bytes": len(file_content)}

            elif operation == "edit_file":
                target_str = kwargs.get("target_string", "")
                replacement = kwargs.get("replacement_string", "")
                if not target.is_file():
                    return ToolResult(success=False, error=f"File '{target}' not found.")
                with open(target, "r", encoding="utf-8") as f:
                    current_content = f.read()
                if target_str not in current_content:
                    return ToolResult(success=False, error=f"Target string not found in '{target}'.")
                new_content = current_content.replace(target_str, replacement, 1)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(new_content)
                res_data = {"status": "edited", "file": str(target)}

            elif operation == "delete":
                if not target.exists():
                    return ToolResult(success=False, error=f"Path '{target}' does not exist.")
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                res_data = {"deleted": str(target)}

            elif operation == "copy":
                if not dest_str:
                    return ToolResult(success=False, error="Destination path required for copy.")
                dest = Path(dest_str).resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                if target.is_dir():
                    shutil.copytree(target, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(target, dest)
                res_data = {"copied_to": str(dest)}

            elif operation == "move" or operation == "rename":
                if not dest_str:
                    return ToolResult(success=False, error="Destination path required for move/rename.")
                dest = Path(dest_str).resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(dest))
                res_data = {"moved_to": str(dest)}

            elif operation == "list_dir":
                if not target.is_dir():
                    return ToolResult(success=False, error=f"Directory '{target}' not found.")
                items = []
                for entry in target.iterdir():
                    items.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else None
                    })
                res_data = {"path": str(target), "items": items}

            elif operation == "search":
                if not target.is_dir():
                    return ToolResult(success=False, error=f"Search root '{target}' is not a directory.")
                matches = []
                for root, dirs, files in os.walk(target):
                    for name in fnmatch.filter(files + dirs, pattern):
                        matches.append(os.path.join(root, name))
                res_data = {"matches": matches[:100]}

            else:
                return ToolResult(success=False, error=f"Unknown filesystem operation: {operation}")

            # Verify the operation
            verif = self.verify(ToolResult(success=True, data=res_data), operation=operation, target=target, dest=dest_str, content=content)

            return ToolResult(
                success=verif.get("verified", True),
                data=res_data,
                verification=verif
            )

        except Exception as ex:
            return ToolResult(success=False, error=f"Filesystem error: {str(ex)}")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        operation = kwargs.get("operation")
        target: Optional[Path] = kwargs.get("target")
        dest_str = kwargs.get("dest")
        dest = Path(dest_str).resolve() if dest_str else None
        content = kwargs.get("content")

        if operation == "create_folder":
            exists = target.is_dir() if target else False
            return {
                "verified": exists,
                "reason": f"Directory {target} verified present." if exists else f"Directory {target} not found after creation."
            }

        elif operation in ["create_file", "write_file"]:
            exists = target.is_file() if target else False
            if exists and content is not None:
                size_ok = target.stat().st_size >= len(content.encode("utf-8"))
                return {
                    "verified": exists and size_ok,
                    "reason": f"File {target} created and size confirmed." if size_ok else "File exists but content size discrepancy."
                }
            return {
                "verified": exists,
                "reason": f"File {target} confirmed present." if exists else "File missing."
            }

        elif operation == "delete":
            deleted = not target.exists() if target else False
            return {
                "verified": deleted,
                "reason": f"Path {target} confirmed removed." if deleted else "Path still exists after deletion attempt."
            }

        elif operation in ["copy", "move", "rename"]:
            dest_exists = dest.exists() if dest else False
            return {
                "verified": dest_exists,
                "reason": f"Destination {dest} verified." if dest_exists else "Destination missing."
            }

        return {"verified": True, "reason": "Operation completed."}
