"""FileSystem Specialist Agent for KritiAI."""
from typing import Any, Dict
from agents.base import AgentAction, BaseAgent
from security.policies.models import RiskLevel


class FileSystemAgent(BaseAgent):
    """Specialized agent for managing files, folders, code structures, and directories."""
    name = "FileSystemAgent"
    description = "Specialist in directory creation, file I/O, file search, and disk operations."
    capabilities = ["create_folder", "create_file", "read_file", "edit_file", "delete_file", "search_files"]
    allowed_tools = ["filesystem"]
    risk_level = RiskLevel.MEDIUM

    def plan_step(self, objective: str, context: Dict[str, Any]) -> AgentAction:
        obj_lower = objective.lower()
        path = context.get("target_path") or context.get("path") or "output"
        content = context.get("content", "")

        if "folder" in obj_lower or "dir" in obj_lower:
            return AgentAction(
                tool_name="filesystem",
                parameters={"operation": "create_folder", "path": path},
                thought=f"Executing folder creation for '{path}' to fulfill objective: {objective}",
                expected_result=f"Directory '{path}' created and verified"
            )
        else:
            return AgentAction(
                tool_name="filesystem",
                parameters={"operation": "create_file", "path": path, "content": content},
                thought=f"Writing file '{path}' to fulfill objective: {objective}",
                expected_result=f"File '{path}' written and verified"
            )
