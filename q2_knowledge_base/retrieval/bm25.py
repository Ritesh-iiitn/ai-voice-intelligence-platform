"""
Lightweight Okapi BM25 keyword retrieval implementation.
"""
import math
import re
from typing import List, Tuple, Dict, Set, Optional, Any
from q2_knowledge_base.schemas.record import ChunkRecord

class BM25Retriever:
    """Okapi BM25 index and retrieval engine for exact keyword matching."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[ChunkRecord] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.term_freqs: List[Dict[str, int]] = []

    STOP_WORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
        "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
        "during", "each", "few", "for", "from", "further", "had", "has", "have", "having",
        "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i",
        "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
        "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
        "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same",
        "she", "should", "so", "some", "such", "t", "than", "that", "the", "their",
        "theirs", "them", "themselves", "then", "there", "these", "they", "this",
        "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
        "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will",
        "with", "you", "your", "yours", "yourself", "yourselves"
    }

    def tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())
        return [w for w in words if w not in self.STOP_WORDS]

    def build_index(self, chunks: List[ChunkRecord]):
        """Index chunks and precompute term frequencies and IDF."""
        self.chunks = list(chunks)
        self.doc_lengths = []
        self.term_freqs = []
        self.doc_freqs = {}

        total_length = 0
        N = len(chunks)
        if N == 0:
            return

        for chunk in chunks:
            tokens = self.tokenize(chunk.content)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_length += length

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs.append(tf)

            for unique_t in tf.keys():
                self.doc_freqs[unique_t] = self.doc_freqs.get(unique_t, 0) + 1

        self.avg_doc_length = total_length / N if N > 0 else 0.0

        # Calculate IDF
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            # Standard smoothed BM25 IDF
            self.idf[term] = math.log(1.0 + (N - freq + 0.5) / (freq + 0.5))

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ChunkRecord, float]]:
        """Compute BM25 scores for query terms."""
        if not self.chunks or not self.idf:
            return []

        tokens = self.tokenize(query)
        if not tokens:
            return []

        scores: List[float] = [0.0] * len(self.chunks)

        for i, tf in enumerate(self.term_freqs):
            doc_len = self.doc_lengths[i]
            len_norm = 1.0 - self.b + self.b * (doc_len / (self.avg_doc_length or 1.0))

            for t in tokens:
                if t in tf:
                    t_freq = tf[t]
                    idf = self.idf.get(t, 0.0)
                    term_score = idf * (t_freq * (self.k1 + 1.0)) / (t_freq + self.k1 * len_norm)
                    scores[i] += term_score

        # Normalize scores to 0.0 - 1.0
        max_score = max(scores) if scores else 0.0
        norm_factor = max_score if max_score > 0 else 1.0

        ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)

        results: List[Tuple[ChunkRecord, float]] = []
        for idx in ranked_indices:
            if scores[idx] <= 0:
                break
            chunk = self.chunks[idx]
            norm_score = scores[idx] / norm_factor

            # Metadata filter check
            if filters:
                match = True
                for k, v in filters.items():
                    val = getattr(chunk, k, None) or chunk.metadata.get(k)
                    if val != v:
                        match = False
                        break
                if not match:
                    continue

            results.append((chunk, norm_score))
            if len(results) >= top_k:
                break

        return results
