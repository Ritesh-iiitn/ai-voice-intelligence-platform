"""
Deduplication module supporting exact duplicate detection (SHA-256)
and near-duplicate detection (token Jaccard similarity) while preserving version lineage.
"""
import hashlib
import re
from typing import List, Dict, Set, Tuple
from q2_knowledge_base.schemas.record import DocumentRecord

class Deduplicator:
    """Detects exact and near duplicates across documents while preserving version history."""

    def __init__(self, near_duplicate_threshold: float = 0.85):
        self.near_duplicate_threshold = near_duplicate_threshold
        self.exact_hashes: Dict[str, DocumentRecord] = {}
        self.document_tokens: Dict[str, Set[str]] = {}
        self.version_lineage: Dict[str, List[DocumentRecord]] = {}

    def compute_exact_hash(self, content: str) -> str:
        """Normalized SHA-256 hash of text content."""
        normalized = re.sub(r"\s+", " ", content.strip().lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def tokenize(self, content: str) -> Set[str]:
        """Extract word shingles/tokens for Jaccard similarity."""
        words = re.findall(r"\b\w{3,}\b", content.lower())
        return set(words)

    def jaccard_similarity(self, set_a: Set[str], set_b: Set[str]) -> float:
        """Compute Jaccard similarity coefficient between two token sets."""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    def process_documents(self, docs: List[DocumentRecord]) -> Tuple[List[DocumentRecord], List[Dict[str, str]]]:
        """
        Filters exact duplicate documents and links version variants.
        Returns:
            kept_docs: List of distinct documents to index.
            duplicate_report: List of reports documenting exact dupes or linked version variants.
        """
        kept_docs: List[DocumentRecord] = []
        reports: List[Dict[str, str]] = []

        for doc in docs:
            content_hash = self.compute_exact_hash(doc.content)
            tokens = self.tokenize(doc.content)

            # 1. Exact Duplicate Check
            if content_hash in self.exact_hashes:
                existing = self.exact_hashes[content_hash]
                reports.append({
                    "type": "exact_duplicate",
                    "doc_id": doc.document_id,
                    "existing_doc_id": existing.document_id,
                    "reason": f"Exact content match with {existing.document_id}"
                })
                continue

            # 2. Near-Duplicate & Version Variant Check
            is_near_dup = False
            for existing_id, existing_tokens in self.document_tokens.items():
                sim = self.jaccard_similarity(tokens, existing_tokens)
                if sim >= self.near_duplicate_threshold:
                    # Check if it's a distinct version
                    existing_doc = next(d for d in kept_docs if d.document_id == existing_id)
                    if existing_doc.version != doc.version:
                        # Legitimate version variant: keep both for historical traceability!
                        reports.append({
                            "type": "version_variant",
                            "doc_id": doc.document_id,
                            "existing_doc_id": existing_id,
                            "similarity": f"{sim:.2f}",
                            "reason": f"Version difference preserved (v{doc.version} vs v{existing_doc.version})"
                        })
                    else:
                        # Near-duplicate with same version: skip to prevent index pollution
                        reports.append({
                            "type": "near_duplicate_skipped",
                            "doc_id": doc.document_id,
                            "existing_doc_id": existing_id,
                            "similarity": f"{sim:.2f}",
                            "reason": f"Near-duplicate of {existing_id} with similarity {sim:.2f}"
                        })
                        is_near_dup = True
                        break

            if not is_near_dup:
                self.exact_hashes[content_hash] = doc
                self.document_tokens[doc.document_id] = tokens
                kept_docs.append(doc)

        return kept_docs, reports
