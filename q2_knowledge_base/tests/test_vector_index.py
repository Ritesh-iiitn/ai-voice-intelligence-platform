import pytest
import numpy as np
from q2_knowledge_base.embeddings.local import LocalVectorEmbeddingProvider
from q2_knowledge_base.indexing.vector_index import VectorIndex
from q2_knowledge_base.schemas.record import ChunkRecord

@pytest.fixture
def sample_chunks():
    return [
        ChunkRecord(
            chunk_id="chk_001",
            document_id="policy_v2",
            title="Policy V2",
            content="Tier 1 credit score 750+ has fixed APR of 6.49%.",
            category="rates",
            product="auto_credit",
            source="policy_v2.txt",
            source_section="1.2 Rates",
            version="2.1"
        ),
        ChunkRecord(
            chunk_id="chk_002",
            document_id="policy_v1",
            title="Policy V1",
            content="Historical Tier 1 credit score 750+ had fixed APR of 7.99%.",
            category="rates",
            product="auto_credit",
            source="policy_v1.txt",
            source_section="1.2 Rates",
            version="1.0"
        ),
        ChunkRecord(
            chunk_id="chk_003",
            document_id="insurance_doc",
            title="Insurance Riders",
            content="Involuntary unemployment coverage covers up to 6 monthly installments.",
            category="insurance",
            product="insurance",
            source="riders.html",
            source_section="Coverage Table",
            version="1.4"
        )
    ]

def test_local_embeddings():
    provider = LocalVectorEmbeddingProvider()
    docs = ["Tier 1 interest rate is 6.49%", "Unemployment insurance rider"]
    vecs = provider.embed_documents(docs)
    assert len(vecs) == 2
    assert len(vecs[0]) > 0
    # Vector should have non-zero norm
    norm = np.linalg.norm(vecs[0])
    assert pytest.approx(norm, 0.01) == 1.0

def test_vector_index_search(sample_chunks):
    provider = LocalVectorEmbeddingProvider()
    index = VectorIndex(embedding_provider=provider)
    index.build_index(sample_chunks)

    results = index.search("What is the interest rate for Tier 1?", top_k=2)
    assert len(results) == 2
    top_chunk, top_score = results[0]
    assert "fixed APR" in top_chunk.content
    assert top_score > 0.0

def test_vector_index_metadata_filtering(sample_chunks):
    provider = LocalVectorEmbeddingProvider()
    index = VectorIndex(embedding_provider=provider)
    index.build_index(sample_chunks)

    # Filter strictly for active version 2.1
    results = index.search("interest rate tier 1", top_k=2, filters={"version": "2.1"})
    assert len(results) == 1
    assert results[0][0].version == "2.1"
    assert results[0][0].chunk_id == "chk_001"

def test_vector_index_save_and_load(sample_chunks, tmp_path):
    save_dir = tmp_path / "test_idx"
    provider = LocalVectorEmbeddingProvider()
    index = VectorIndex(embedding_provider=provider)
    index.build_index(sample_chunks)
    index.save(str(save_dir))

    # Load in new index
    loaded_index = VectorIndex(embedding_provider=provider)
    loaded_index.load(str(save_dir))
    assert len(loaded_index.chunks) == 3
    assert loaded_index.vectors is not None
    assert loaded_index.vectors.shape[0] == 3
