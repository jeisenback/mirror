from typing import List, Dict, Any, Tuple
import math


class InMemoryVectorStore:
    """A tiny in-memory 'vector' store that uses simple bag-of-words counts
    as vectors. This is a placeholder for Chroma/FAISS integration in production.
    """

    def __init__(self):
        self.docs: List[Dict[str, Any]] = []
        self.vectors: List[Dict[str, int]] = []

    def _doc_vector(self, text: str) -> Dict[str, int]:
        vec = {}
        for tok in text.split():
            vec[tok] = vec.get(tok, 0) + 1
        return vec

    def index(self, docs: List[Dict[str, Any]]):
        for d in docs:
            text = d.get('text') or d.get('content') or ''
            self.docs.append(d)
            self.vectors.append(self._doc_vector(text))

    def _cosine(self, a: Dict[str, int], b: Dict[str, int]) -> float:
        # dot / (|a||b|)
        dot = 0
        for k, v in a.items():
            dot += v * b.get(k, 0)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        qv = self._doc_vector(query_text)
        scored = []
        for doc, vec in zip(self.docs, self.vectors):
            score = self._cosine(qv, vec)
            scored.append((doc, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
