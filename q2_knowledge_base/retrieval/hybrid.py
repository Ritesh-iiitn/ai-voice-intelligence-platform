"""
Hybrid retrieval engine combining dense vector search and BM25 keyword matching with RRF ranking.
"""
from typing import List, Dict, Any, Optional
from q2_knowledge_base.schemas.record import ChunkRecord, RetrievalResult
from q2_knowledge_base.indexing.vector_index import VectorIndex
from q2_knowledge_base.retrieval.bm25 import BM25Retriever
from q2_knowledge_base.cleaning.normalizer import TerminologyNormalizer

class HybridRetriever:
    """Hybrid semantic + keyword retriever with Reciprocal Rank Fusion and confidence thresholding."""

    def __init__(
        self,
        vector_index: VectorIndex,
        bm25_retriever: BM25Retriever,
        normalizer: Optional[TerminologyNormalizer] = None,
        confidence_threshold: float = 0.25,
        rrf_k: int = 60
    ):
        self.vector_index = vector_index
        self.bm25_retriever = bm25_retriever
        self.normalizer = normalizer or TerminologyNormalizer()
        self.confidence_threshold = confidence_threshold
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        apply_threshold: bool = True
    ) -> List[RetrievalResult]:
        """
        Execute hybrid retrieval across dense vector and BM25 indices.
        """
        # Step 1: Query normalization & synonym expansion
        normalized_query = self.normalizer.normalize_query(query)

        # Step 2: Dense vector retrieval
        vector_candidates = self.vector_index.search(normalized_query, top_k=top_k * 2, filters=filters)
        
        # Step 3: BM25 keyword retrieval
        bm25_candidates = self.bm25_retriever.search(normalized_query, top_k=top_k * 2, filters=filters)

        # Step 4: Reciprocal Rank Fusion (RRF)
        chunk_map: Dict[str, ChunkRecord] = {}
        rrf_scores: Dict[str, float] = {}
        score_types: Dict[str, str] = {}

        for rank, (chunk, score) in enumerate(vector_candidates):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            # Vector contribution weighted by actual similarity
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1)) * score * 1.2
            score_types[cid] = "semantic"

        for rank, (chunk, score) in enumerate(bm25_candidates):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            # Keyword contribution weighted by BM25 score
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1)) * score * 1.0
            if cid in score_types and score_types[cid] == "semantic":
                score_types[cid] = "hybrid"
            else:
                score_types[cid] = "keyword"

        if not rrf_scores:
            return []

        # Normalize RRF scores to 0.0 - 1.0 relative to theoretical maximum
        max_possible = (1.0 / (self.rrf_k + 1)) * 2.2
        ranked_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        results: List[RetrievalResult] = []
        for cid in ranked_chunk_ids:
            raw_score = rrf_scores[cid]
            norm_score = min(1.0, raw_score / max_possible)

            if apply_threshold and norm_score < self.confidence_threshold:
                continue

            chunk = chunk_map[cid]
            results.append(RetrievalResult(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                source=chunk.source,
                section=chunk.source_section,
                version=chunk.version,
                score=round(norm_score, 4),
                retrieval_type=score_types.get(cid, "hybrid"),
                metadata=chunk.metadata
            ))

            if len(results) >= top_k:
                break

        return results
