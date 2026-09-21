"""
In-memory vector index with cosine similarity, metadata filtering, and serialization.
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from q2_knowledge_base.schemas.record import ChunkRecord
from q2_knowledge_base.embeddings.base import BaseEmbeddingProvider

class VectorIndex:
    """Vector index supporting dense similarity lookup and metadata filtering."""

    def __init__(self, embedding_provider: BaseEmbeddingProvider):
        self.embedding_provider = embedding_provider
        self.chunks: List[ChunkRecord] = []
        self.vectors: Optional[np.ndarray] = None

    def build_index(self, chunks: List[ChunkRecord]):
        """Index a list of chunks and compute their embedding vectors."""
        if not chunks:
            return

        self.chunks = list(chunks)
        texts = [c.content for c in chunks]

        # Fit embedding provider if required
        if hasattr(self.embedding_provider, "fit"):
            self.embedding_provider.fit(texts)

        vecs = self.embedding_provider.embed_documents(texts)
        self.vectors = np.array(vecs, dtype=np.float32)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ChunkRecord, float]]:
        """
        Search for top_k most similar chunks using cosine similarity.
        Optionally apply metadata filters (e.g. version, product, category).
        """
        if not self.chunks or self.vectors is None or len(self.chunks) == 0:
            return []

        query_vec = np.array(self.embedding_provider.embed_query(query), dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm == 0:
            return []

        # Vector norms
        v_norms = np.linalg.norm(self.vectors, axis=1)
        # Avoid division by zero
        v_norms[v_norms == 0] = 1e-9

        scores = np.dot(self.vectors, query_vec) / (v_norms * q_norm)

        # Rank all candidates
        ranked_indices = np.argsort(scores)[::-1]

        results: List[Tuple[ChunkRecord, float]] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score < 0.05:
                # Discard candidates with negligible similarity
                break

            chunk = self.chunks[idx]

            # Apply metadata filters if provided
            if filters:
                match = True
                for k, v in filters.items():
                    val = getattr(chunk, k, None) or chunk.metadata.get(k)
                    if val != v:
                        match = False
                        break
                if not match:
                    continue

            results.append((chunk, score))
            if len(results) >= top_k:
                break

        return results

    def save(self, directory: str):
        """Serialize index and metadata to disk."""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        # Save chunks
        chunks_data = [c.model_dump() for c in self.chunks]
        with open(path / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2)

        # Save vectors
        if self.vectors is not None:
            np.save(path / "vectors.npy", self.vectors)

    def load(self, directory: str):
        """Load serialized index from disk."""
        path = Path(directory)
        chunks_file = path / "chunks.json"
        vecs_file = path / "vectors.npy"

        if chunks_file.exists():
            with open(chunks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.chunks = [ChunkRecord(**d) for d in data]

        if vecs_file.exists():
            self.vectors = np.load(vecs_file)
