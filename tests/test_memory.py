"""Tests for Memory Subsystem and Local Vector Search."""
from pathlib import Path
from database.connection import DatabaseConnection
from database.repository import Repository
from memory.base import MemoryTier
from memory.manager import MemoryManager


def test_memory_storage_and_recall(tmp_path: Path):
    db_conn = DatabaseConnection(db_path=tmp_path / "test_memory.db")
    repo = Repository(db=db_conn)
    mem_mgr = MemoryManager(repo=repo)

    # Add user preference
    mem_mgr.remember(
        tier=MemoryTier.USER,
        key="preferred_language",
        content="User prefers Python and local-first execution."
    )

    # Add project context
    mem_mgr.remember(
        tier=MemoryTier.PROJECT,
        key="project_tech",
        content="KritiAI is built using FastAPI and Python on Windows."
    )

    # Search
    results = mem_mgr.recall("Python execution", top_k=2)
    assert len(results) > 0
    contents = [r.content for r in results]
    assert any("Python" in c for c in contents)
