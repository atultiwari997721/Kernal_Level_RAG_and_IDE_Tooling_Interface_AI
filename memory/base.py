"""Memory Base Definitions and Interfaces."""
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel


class MemoryTier(str, Enum):
    """Different levels and lifetimes of memory in KritiAI."""
    CONVERSATION = "conversation"
    USER = "user"
    PROJECT = "project"
    TASK = "task"
    LONG_TERM = "long_term"


class MemoryEntry(BaseModel):
    """Single unit of stored memory."""
    id: str
    tier: MemoryTier
    key: Optional[str] = None
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    similarity_score: Optional[float] = None
