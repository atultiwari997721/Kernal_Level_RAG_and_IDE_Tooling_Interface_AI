"""Multi-Tier Memory Coordinator for KritiAI."""
from typing import Any, Dict, List, Optional
from database.repository import Repository
from memory.base import MemoryEntry, MemoryTier
from memory.vector_store import LocalVectorStore


class MemoryManager:
    """Coordinates Conversation, User, Project, Task, and Long-Term Memory."""

    def __init__(self, repo: Optional[Repository] = None):
        self.repo = repo or Repository()
        self.vector_store = LocalVectorStore()
        self._load_vector_index()

    def _load_vector_index(self) -> None:
        """Hydrate vector index from persistent SQLite store."""
        entries = self.repo.get_memories(limit=1000)
        for entry in entries:
            self.vector_store.add_document(
                doc_id=entry["id"],
                text=f"{entry.get('key', '')} {entry['content']}",
                metadata={"tier": entry["tier"], "key": entry.get("key")}
            )

    def remember(
        self,
        tier: MemoryTier,
        content: str,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """Store a memory item across persistent database and in-memory vector index."""
        result = self.repo.add_memory(
            tier=tier.value,
            content=content,
            key=key,
            metadata=metadata
        )
        self.vector_store.add_document(
            doc_id=result["id"],
            text=f"{key or ''} {content}",
            metadata={"tier": tier.value, "key": key}
        )
        return MemoryEntry(
            id=result["id"],
            tier=tier,
            key=key,
            content=content,
            metadata=metadata,
            created_at=result["created_at"]
        )

    def recall(
        self,
        query: str,
        tier: Optional[MemoryTier] = None,
        top_k: int = 5
    ) -> List[MemoryEntry]:
        """Search relevant memories using vector similarity and tier filtering."""
        search_results = self.vector_store.search(query, top_k=top_k * 2)
        matched_ids = []
        scores: Dict[str, float] = {}

        for doc_id, score, data in search_results:
            if tier is None or data.get("metadata", {}).get("tier") == tier.value:
                matched_ids.append(doc_id)
                scores[doc_id] = score
                if len(matched_ids) >= top_k:
                    break

        if not matched_ids:
            # Fallback to recent items in SQLite if no vector match
            recent = self.repo.get_memories(tier=tier.value if tier else None, limit=top_k)
            return [
                MemoryEntry(
                    id=r["id"],
                    tier=MemoryTier(r["tier"]),
                    key=r.get("key"),
                    content=r["content"],
                    metadata=r.get("metadata"),
                    created_at=r["created_at"],
                    similarity_score=0.0
                )
                for r in recent
            ]

        # Retrieve full records
        all_memories = self.repo.get_memories(limit=500)
        id_map = {m["id"]: m for m in all_memories}

        results: List[MemoryEntry] = []
        for m_id in matched_ids:
            if m_id in id_map:
                m = id_map[m_id]
                results.append(
                    MemoryEntry(
                        id=m["id"],
                        tier=MemoryTier(m["tier"]),
                        key=m.get("key"),
                        content=m["content"],
                        metadata=m.get("metadata"),
                        created_at=m["created_at"],
                        similarity_score=round(scores.get(m_id, 0.0), 3)
                    )
                )
        return results

    def list_memories(self, tier: Optional[MemoryTier] = None) -> List[Dict[str, Any]]:
        return self.repo.get_memories(tier=tier.value if tier else None)

    def delete_memory(self, memory_id: str) -> bool:
        self.vector_store.delete_document(memory_id)
        return self.repo.delete_memory(memory_id)

    def clear(self, tier: Optional[MemoryTier] = None) -> int:
        self.vector_store.clear()
        count = self.repo.clear_memory(tier=tier.value if tier else None)
        self._load_vector_index()
        return count
