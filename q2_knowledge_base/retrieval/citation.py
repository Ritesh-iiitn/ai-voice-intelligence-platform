"""
Citation formatting and verification module.
"""
from typing import List, Dict, Any
from pathlib import Path
from q2_knowledge_base.schemas.record import RetrievalResult

class CitationFormatter:
    """Formats and validates source citations for retrieved chunks."""

    @staticmethod
    def format_citation(result: RetrievalResult) -> str:
        """Format a single citation string."""
        source_name = Path(result.source).name
        return f"[Source: {source_name} | Section: {result.section} | Version: {result.version}]"

    @staticmethod
    def format_grounded_context(results: List[RetrievalResult]) -> str:
        """
        Format a list of retrieval results into grounded context block
        for LLM prompt or answer verification.
        """
        if not results:
            return "No verified knowledge base information retrieved."

        blocks = []
        for i, res in enumerate(results, start=1):
            citation = CitationFormatter.format_citation(res)
            blocks.append(
                f"--- EXCERPT {i} ---\n"
                f"{citation}\n"
                f"{res.content.strip()}\n"
            )

        return "\n".join(blocks)
