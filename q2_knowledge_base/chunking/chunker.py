"""
Semantic section-aware chunker preserving header hierarchy, policy context, and tables.
"""
import re
from typing import List, Dict, Any, Optional
from q2_knowledge_base.schemas.record import DocumentRecord, ChunkRecord

class SemanticSectionChunker:
    """Chunks documents along semantic section and tabular boundaries rather than fixed token splits."""

    SECTION_HEADER_REGEX = re.compile(
        r"^(?:(?:[0-9]{1,2}\.[0-9]{0,2}\s+[A-Za-z0-9\s,&/\(\)\-]+:?)|(?:#{1,4}\s+[^\n]+)|(?:\[Record\s+\d+\])|(?:SECTION\s+[0-9A-Za-z\s]+:?))$",
        re.M
    )

    def __init__(self, max_chunk_chars: int = 1500, min_chunk_chars: int = 100):
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars

    def chunk_document(self, doc: DocumentRecord) -> List[ChunkRecord]:
        """Convert a DocumentRecord into semantic ChunkRecord objects."""
        if not doc.content or doc.status != "success":
            return []

        chunks: List[ChunkRecord] = []
        raw_sections = self._split_into_sections(doc.content)

        chunk_idx = 0
        current_header = doc.title

        for section_title, section_body in raw_sections:
            if section_title:
                current_header = section_title

            # If section contains tabular markdown, keep table intact
            if "|" in section_body and "\n|" in section_body:
                chunk_text = f"[{doc.title} > {current_header}]\n{section_body.strip()}"
                chunks.append(self._create_chunk(doc, chunk_text, current_header, chunk_idx))
                chunk_idx += 1
                continue

            # Split large sections by paragraphs
            paragraphs = section_body.split("\n\n")
            buffer = ""

            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean:
                    continue

                if len(buffer) + len(p_clean) < self.max_chunk_chars:
                    buffer = f"{buffer}\n\n{p_clean}" if buffer else p_clean
                else:
                    if buffer:
                        chunk_text = f"[{doc.title} > {current_header}]\n{buffer.strip()}"
                        chunks.append(self._create_chunk(doc, chunk_text, current_header, chunk_idx))
                        chunk_idx += 1
                    buffer = p_clean

            if buffer:
                chunk_text = f"[{doc.title} > {current_header}]\n{buffer.strip()}"
                chunks.append(self._create_chunk(doc, chunk_text, current_header, chunk_idx))
                chunk_idx += 1

        return chunks

    def _split_into_sections(self, content: str) -> List[tuple]:
        """Splits text by regex section headers into (header, body) tuples."""
        matches = list(self.SECTION_HEADER_REGEX.finditer(content))
        if not matches:
            return [("General Information", content)]

        sections = []
        # Any text before the first header
        if matches[0].start() > 0:
            preamble = content[:matches[0].start()].strip(" \n-=")
            if preamble:
                sections.append(("Preamble", preamble))

        for i, match in enumerate(matches):
            raw_header = match.group(0)
            header = re.sub(r"[-=]+", "", raw_header).strip(" #\n*:-")
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start:end].strip(" \n-=")
            if body:
                sections.append((header, body))

        return sections

    def _create_chunk(self, doc: DocumentRecord, content: str, section: str, idx: int) -> ChunkRecord:
        # Determine product and category from title / section
        product = "auto_and_personal_credit"
        category = "underwriting_and_policy"
        if "insurance" in doc.title.lower() or "rider" in doc.title.lower():
            product = "credit_protection_insurance"
            category = "insurance_coverage"
        elif "faq" in doc.title.lower():
            category = "faq_and_objections"

        return ChunkRecord(
            chunk_id=f"{doc.document_id}_chk_{idx:03d}",
            document_id=doc.document_id,
            title=doc.title,
            content=content,
            category=category,
            product=product,
            source=doc.source,
            source_section=section,
            version=doc.version,
            effective_date=doc.effective_date,
            expiry_date=doc.expiry_date,
            contains_pii=doc.contains_pii,
            pii_types=doc.pii_types,
            metadata={
                "source_type": doc.source_type,
                "chunk_index": idx
            }
        )
