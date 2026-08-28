"""Local-First Lightweight Vector Storage Abstraction."""
import math
import re
from typing import Any, Dict, List, Optional, Tuple


class LocalVectorStore:
    """Zero-dependency local vector store using TF-IDF / term-frequency cosine similarity."""

    def __init__(self) -> None:
        self._documents: Dict[str, Dict[str, Any]] = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        tf: Dict[str, float] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0.0) + 1.0
        # Normalize
        norm = math.sqrt(sum(v * v for v in tf.values()))
        if norm > 0:
            for k in tf:
                tf[k] /= norm
        return tf

    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        tokens = self._tokenize(text)
        tf = self._compute_tf(tokens)
        self._documents[doc_id] = {
            "text": text,
            "tf": tf,
            "metadata": metadata or {}
        }

    def delete_document(self, doc_id: str) -> bool:
        return self._documents.pop(doc_id, None) is not None

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        query_tokens = self._tokenize(query)
        query_tf = self._compute_tf(query_tokens)
        if not query_tf:
            return []

        scores: List[Tuple[str, float, Dict[str, Any]]] = []
        for doc_id, doc_data in self._documents.items():
            doc_tf = doc_data["tf"]
            # Cosine similarity between normalized vectors
            score = sum(query_tf.get(t, 0.0) * doc_tf.get(t, 0.0) for t in query_tf)
            if score > 0:
                scores.append((doc_id, score, doc_data))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def clear(self) -> None:
        self._documents.clear()
