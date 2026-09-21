import pytest
from q2_knowledge_base.ingestion.reader import DocumentIngestor
from q2_knowledge_base.chunking.chunker import SemanticSectionChunker

@pytest.fixture
def chunker():
    return SemanticSectionChunker()

@pytest.fixture
def ingestor():
    return DocumentIngestor()

def test_semantic_chunking_preserves_headers(chunker, ingestor):
    doc = ingestor.ingest_file("data/source_documents/credit_lending_policy_v2.txt")
    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 3
    
    # Check that chunks retain header breadcrumb
    assert any("product overview" in c.source_section.lower() or "product overview" in c.content.lower() for c in chunks)
    assert any("fees" in c.source_section.lower() or "fees" in c.content.lower() for c in chunks)
    
    # Check chunk schema integrity
    first = chunks[0]
    assert first.chunk_id.startswith("credit_lending_policy_v2_chk_")
    assert first.version == "2.1"
    assert first.source.endswith("credit_lending_policy_v2.txt")

def test_semantic_chunking_preserves_table(chunker, ingestor):
    doc = ingestor.ingest_file("data/source_documents/insurance_protection_riders.html")
    chunks = chunker.chunk_document(doc)
    
    table_chunk = next((c for c in chunks if "Involuntary Unemployment" in c.content), None)
    assert table_chunk is not None
    # Verify table columns exist together in the chunk
    assert "Total & Permanent Disability (TPD)" in table_chunk.content
    assert "Multi-Vehicle Household Bundle" in table_chunk.content
