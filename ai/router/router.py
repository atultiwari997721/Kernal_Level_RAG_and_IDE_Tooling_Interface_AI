"""Intelligent Model Router with User Overrides and Current Affairs Routing."""
import re
from typing import Any, Dict, List, Optional, Tuple
from ai.gateway.gateway import ModelGateway
from config.settings import AppConfig, get_config


class ModelRouter:
    """Selects the optimal model based on task category, privacy, cost, and user overrides."""

    def __init__(self, gateway: Optional[ModelGateway] = None, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self.gateway = gateway or ModelGateway(self.config)

    @staticmethod
    def is_current_affairs_query(query: str) -> bool:
        """Detect whether a query asks about current affairs, latest news, or contemporary events."""
        if not query or not query.strip():
            return False
        q = query.lower().strip()

        # Direct current affairs & news key phrases
        keywords = [
            "current affairs", "latest topic", "latest topics", "latest news", "breaking news",
            "recent news", "today's news", "today news", "trending topic", "trending news",
            "headlines", "current events", "current situation", "latest update", "latest updates",
            "recent developments", "latest developments", "newest update", "what happened today",
            "what happened yesterday", "what happened recently", "recent events",
            "current prime minister", "current president", "current chief minister",
            "current election", "recent election", "who is the current", "who is current",
            "latest release", "released this week", "released today", "ai in 2025", "ai in 2026",
            "developments in 2025", "developments in 2026", "world news", "geopolitics",
            "stock market today", "budget 2025", "budget 2026", "olympics", "championship"
        ]
        if any(k in q for k in keywords):
            return True

        # Regex patterns for contemporary queries
        patterns = [
            r"\b(?:latest|newest|recent|current)\s+(?:news|updates?|affairs?|events?|trends?|happenings?|status|situation|developments?)\b",
            r"\bwhat(?:'s|\s+is)\s+(?:happening|the\s+latest|new)\s+(?:in|with|at|regarding)\b",
            r"\bwho\s+won\s+(?:the\s+)?(?:recent|latest|current|\d{4})\b",
            r"\b(?:2025|2026)\s+(?:election|summit|news|updates|affairs|developments)\b",
        ]
        for pat in patterns:
            if re.search(pat, q):
                return True

        return False

    def route_current_affairs(self, query: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """Route current affairs queries specifically to Qwen or DeepSeek models."""
        models = self.gateway.list_all_models()

        # 1. Look for a Qwen 7B model in discovered models
        for m in models:
            mid = m["id"].lower()
            if "qwen" in mid and ("7b" in mid or "2.5" in mid):
                return self._resolve_composite_id(m["id"])

        # 2. Look for any DeepSeek model in discovered models
        for m in models:
            mid = m["id"].lower()
            if "deepseek" in mid:
                return self._resolve_composite_id(m["id"])

        # 3. Look for any Qwen model
        for m in models:
            mid = m["id"].lower()
            if "qwen" in mid:
                return self._resolve_composite_id(m["id"])

        # 4. Check available providers
        available = self.gateway.list_available_providers()
        if "ollama" in available:
            return "ollama", "qwen2.5:7b"
        elif "openai_compatible" in available:
            return "openai_compatible", "deepseek-chat"

        # Fallback to local offline provider with Qwen emulation
        return "offline_local", "qwen2.5:7b-emulated"

    def route_best_coding_model(self) -> Tuple[str, Optional[str]]:
        """Select the highest-capability coding model available for maximum performance in Risk Mode."""
        models = self.gateway.list_all_models()

        # Priority 1: Dedicated coder models (e.g., qwen2.5-coder, deepseek-coder, codellama, starcoder)
        for m in models:
            mid = m["id"].lower()
            if any(k in mid for k in ["qwen2.5-coder", "deepseek-coder", "codellama", "starcoder", "code-"]):
                return self._resolve_composite_id(m["id"])

        # Priority 2: High-reasoning coding models (deepseek-r1, qwen2.5, gpt-4o, claude)
        for m in models:
            mid = m["id"].lower()
            if any(k in mid for k in ["deepseek-r1", "qwen2.5", "gpt-4o", "claude"]):
                return self._resolve_composite_id(m["id"])

        # Priority 3: Any model with 'code' or 'coder'
        for m in models:
            mid = m["id"].lower()
            if "code" in mid or "coder" in mid:
                return self._resolve_composite_id(m["id"])

        # Priority 4: If Ollama is available
        available = self.gateway.list_available_providers()
        if "ollama" in available:
            return "ollama", "qwen2.5-coder:7b"
        elif "openai_compatible" in available:
            return "openai_compatible", "deepseek-coder"

        return "offline_local", "qwen2.5:7b-emulated"

    def route_chat_default(self) -> Tuple[str, Optional[str]]:
        """Return the default model for chat: Qwen 7B."""
        models = self.gateway.list_all_models()

        # Look for Qwen 7B in discovered models
        for m in models:
            mid = m["id"].lower()
            if "qwen" in mid and ("7b" in mid or "2.5" in mid):
                return self._resolve_composite_id(m["id"])

        # Look for any Qwen model
        for m in models:
            mid = m["id"].lower()
            if "qwen" in mid:
                return self._resolve_composite_id(m["id"])

        # If Ollama available
        if "ollama" in self.gateway.list_available_providers():
            return "ollama", "qwen2.5:7b"

        return "offline_local", "qwen2.5:7b-emulated"

    def route(
        self,
        task_type: str = "general",
        query: Optional[str] = None,
        power_mode: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Determine (provider_name, model_name) for a given task type or query."""
        # 1. Current Affairs & Latest Topics detection
        if task_type == "current_affairs" or (query and self.is_current_affairs_query(query)):
            return self.route_current_affairs(query)

        # 2. Chat mode default
        if task_type == "chat":
            return self.route_chat_default()

        # 3. Dynamic Coding Model Escalation: ONLY in Risk Mode!
        active_power = (power_mode or self.config.power_mode.value).lower()
        if task_type == "coding" and active_power == "risk":
            return self.route_best_coding_model()

        models_cfg = self.config.models

        # 4. Check User Overrides
        if task_type == "coding" and models_cfg.coding_model not in ("auto", ""):
            return self._resolve_model_string(models_cfg.coding_model)
        elif task_type == "reasoning" and models_cfg.reasoning_model not in ("auto", ""):
            return self._resolve_model_string(models_cfg.reasoning_model)
        elif task_type == "vision" and models_cfg.vision_model not in ("auto", ""):
            return self._resolve_model_string(models_cfg.vision_model)
        elif models_cfg.general_model not in ("auto", ""):
            return self._resolve_model_string(models_cfg.general_model)

        # 5. Privacy Policy
        if self.config.privacy.prefer_local_models or self.config.privacy.never_send_local_files_to_cloud:
            if "ollama" in self.gateway.list_available_providers():
                return "ollama", "qwen2.5:7b"
            return "offline_local", "kriti-offline-core-v1"

        # 6. Available Provider Routing
        available = self.gateway.list_available_providers()
        if "ollama" in available:
            return "ollama", "qwen2.5:7b"
        elif "openai_compatible" in available:
            return "openai_compatible", models_cfg.openai_model

        return "offline_local", "kriti-offline-core-v1"

    def _resolve_composite_id(self, composite_id: str) -> Tuple[str, Optional[str]]:
        if ":" in composite_id:
            parts = composite_id.split(":", 1)
            return parts[0], parts[1]
        return "offline_local", composite_id

    def _resolve_model_string(self, model_str: str) -> Tuple[str, Optional[str]]:
        """Extract provider and model from strings like 'ollama/llama3.2' or 'gpt-4o'."""
        if "/" in model_str:
            parts = model_str.split("/", 1)
            return parts[0], parts[1]
        if ":" in model_str:
            parts = model_str.split(":", 1)
            return parts[0], parts[1]
        if "gpt-" in model_str or "claude-" in model_str:
            return "openai_compatible", model_str
        return "offline_local", model_str
