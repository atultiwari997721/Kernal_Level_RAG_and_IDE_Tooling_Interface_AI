"""Offline Local Intelligence Provider for KritiAI (Zero-Cloud Out of the Box)."""
import re
import time
from typing import Any, Dict, List, Optional
from ai.providers.base import BaseModelProvider, ModelResponse


class OfflineIntelligenceProvider(BaseModelProvider):
    """Local offline rule-and-intent engine guaranteeing KritiAI functions offline without cloud."""
    name = "offline_local"

    def is_available(self) -> bool:
        return True

    def list_models(self) -> List[str]:
        return ["kriti-offline-core-v1", "kriti-rule-intent-fast"]

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        start_t = time.time()
        last_message = messages[-1]["content"] if messages else ""
        content_lower = last_message.lower().strip()

        tool_calls: List[Dict[str, Any]] = []
        response_text = ""

        # Check for Folder Creation intent: "create a folder called Test", "mkdir Test"
        folder_match = re.search(r"(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)\s+(?:called|named\s+)?([^\s\.\,\;]+)", content_lower)
        if folder_match:
            folder_name = folder_match.group(1).strip("\"'")
            tool_calls.append({
                "id": "call_folder_1",
                "type": "function",
                "function": {
                    "name": "filesystem",
                    "arguments": {
                        "operation": "create_folder",
                        "path": folder_name
                    }
                }
            })
            response_text = f"I will create the directory '{folder_name}' on your Windows system and verify its creation."

        # Check for File Creation intent: "create a file called hello.txt with content ..."
        elif re.search(r"(?:create|make|write)\s+(?:a\s+)?file\s+(?:called|named\s+)?([^\s\,]+)", content_lower):
            file_match = re.search(r"(?:create|make|write)\s+(?:a\s+)?file\s+(?:called|named\s+)?([^\s\,]+)", content_lower)
            file_name = file_match.group(1).strip("\"'") if file_match else "test.txt"
            content_match = re.search(r"(?:with\s+content|containing)\s+[\"']?(.*?)[\"']?$", last_message, re.IGNORECASE)
            file_content = content_match.group(1) if content_match else "# Created by KritiAI\n"
            tool_calls.append({
                "id": "call_file_1",
                "type": "function",
                "function": {
                    "name": "filesystem",
                    "arguments": {
                        "operation": "create_file",
                        "path": file_name,
                        "content": file_content
                    }
                }
            })
            response_text = f"I am creating file '{file_name}' and verifying its contents."

        # Check for Application Launch: "open notepad", "launch calculator"
        elif re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_-]+)", content_lower):
            app_match = re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_-]+)", content_lower)
            app_name = app_match.group(1) if app_match else "notepad"
            if app_name in ["notepad", "calc", "calculator", "edge", "chrome", "code", "vscode", "terminal"]:
                tool_calls.append({
                    "id": "call_app_1",
                    "type": "function",
                    "function": {
                        "name": "app_manager",
                        "arguments": {
                            "action": "launch",
                            "app_name": app_name
                        }
                    }
                })
                response_text = f"Launching application '{app_name}' and verifying process."

        # Check for Hardware / System info: "system info", "check hardware"
        elif "system info" in content_lower or "hardware" in content_lower:
            tool_calls.append({
                "id": "call_sys_1",
                "type": "function",
                "function": {
                    "name": "system_info",
                    "arguments": {"detailed": True}
                }
            })
            response_text = "Inspecting Windows hardware specifications and memory configuration."

        # General conversational response
        if not response_text:
            if "hello" in content_lower or "hi" in content_lower:
                response_text = "Hello! I am KritiAI, your local-first Windows-native autonomous AI execution assistant. Give me a goal, or ask a question."
            elif "who are you" in content_lower:
                response_text = "I am KritiAI, an open-source, local-first Windows execution platform. I can plan and execute real tasks on your PC with full verification."
            else:
                response_text = f"Understood: '{last_message}'. KritiAI is operating in local-first execution mode."

        latency = round((time.time() - start_t) * 1000, 2)
        return ModelResponse(
            content=response_text,
            model=model or "kriti-offline-core-v1",
            tool_calls=tool_calls if tool_calls else None,
            latency_ms=latency
        )
