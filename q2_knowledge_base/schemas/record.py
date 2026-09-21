"""
Schema definitions for documents, chunks, and retrieval records.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentRecord(BaseModel):
    """Normalized representation of an ingested raw document."""
    document_id: str
    title: str
    source: str
    source_type: str  # pdf, txt, html, csv, docx
    version: str = "1.0"
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"  # success, failed, empty, malformed
    error_message: Optional[str] = None
    contains_pii: bool = False
    pii_types: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ChunkRecord(BaseModel):
    """Section-aware semantic chunk with retrieval metadata."""
    chunk_id: str
    document_id: str
    title: str
    content: str
    category: str = "general"
    product: str = "lending"
    source: str
    source_section: str
    version: str = "1.0"
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    contains_pii: bool = False
    pii_types: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class RetrievalResult(BaseModel):
    """Result returned by hybrid retrieval engine with citation."""
    chunk_id: str
    content: str
    source: str
    section: str
    version: str
    score: float
    retrieval_type: str  # semantic, keyword, hybrid
    metadata: Dict[str, Any] = Field(default_factory=dict)
