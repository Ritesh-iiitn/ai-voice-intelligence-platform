"""
Local deterministic vector embedding provider using dense sublinear TF-IDF with L2 normalization.
Zero network calls, fast execution, completely offline-compatible.
"""
import numpy as np
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from q2_knowledge_base.embeddings.base import BaseEmbeddingProvider

class LocalVectorEmbeddingProvider(BaseEmbeddingProvider):
    """Dense vector embedding provider based on scikit-learn TF-IDF with L2 unit normalization."""

    def __init__(self, max_features: int = 1024):
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=max_features,
            token_pattern=r"(?u)\b\w+\b"
        )
        self.is_fitted = False

    def fit(self, texts: List[str]):
        """Fit vocabulary on corpus texts."""
        if not texts:
            return
        self.vectorizer.fit(texts)
        self.is_fitted = True

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed document texts into normalized vectors."""
        if not texts:
            return []
        if not self.is_fitted:
            self.fit(texts)

        matrix = self.vectorizer.transform(texts).toarray()
        return matrix.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query into a normalized vector."""
        if not self.is_fitted:
            # Fit on query as fallback
            self.fit([text])

        vec = self.vectorizer.transform([text]).toarray()[0]
        return vec.tolist()
