import pytest
from q2_knowledge_base.ingestion.reader import DocumentIngestor
from q2_knowledge_base.chunking.chunker import SemanticSectionChunker
from q2_knowledge_base.embeddings.local import LocalVectorEmbeddingProvider
from q2_knowledge_base.indexing.vector_index import VectorIndex
from q2_knowledge_base.retrieval.bm25 import BM25Retriever
from q2_knowledge_base.retrieval.hybrid import HybridRetriever
from q2_knowledge_base.retrieval.citation import CitationFormatter

@pytest.fixture(scope="module")
def hybrid_engine():
    ingestor = DocumentIngestor()
    chunker = SemanticSectionChunker()

    docs = ingestor.ingest_directory("data/source_documents")
    all_chunks = []
    for d in docs:
        if d.status == "success":
            all_chunks.extend(chunker.chunk_document(d))

    embedder = LocalVectorEmbeddingProvider()
    vector_idx = VectorIndex(embedding_provider=embedder)
    vector_idx.build_index(all_chunks)

    bm25 = BM25Retriever()
    bm25.build_index(all_chunks)

    return HybridRetriever(
        vector_index=vector_idx,
        bm25_retriever=bm25,
        confidence_threshold=0.20
    )

def test_retrieval_apr_rates(hybrid_engine):
    results = hybrid_engine.retrieve("What is the interest rate for Tier 1 credit score?", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "6.49%" in top.content or "Tier 1" in top.content
    assert top.score > 0.3
    citation = CitationFormatter.format_citation(top)
    assert "Source:" in citation
    assert "Section:" in citation
    assert "Version:" in citation

def test_retrieval_prepayment_penalty(hybrid_engine):
    results = hybrid_engine.retrieve("Is there any prepayment penalty if I settle early?", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "$0" in top.content or "prepayment" in top.content.lower()

def test_retrieval_unemployment_protection(hybrid_engine):
    results = hybrid_engine.retrieve("Does insurance cover me if I lose my job?", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "Involuntary Unemployment" in top.content or "installments" in top.content

def test_out_of_scope_query_suppressed_by_threshold(hybrid_engine):
    # Query completely unrelated to banking / loans
    results = hybrid_engine.retrieve("How do I bake sourdough bread in an oven?", top_k=3, apply_threshold=True)
    # Either empty or low score below confident threshold
    for r in results:
        assert r.score < 0.45
