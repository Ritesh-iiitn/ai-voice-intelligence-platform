import pytest
from q2_knowledge_base.schemas.record import DocumentRecord
from q2_knowledge_base.deduplication.dedup import Deduplicator

@pytest.fixture
def dedup():
    return Deduplicator(near_duplicate_threshold=0.80)

def test_exact_duplicate_detection(dedup):
    doc1 = DocumentRecord(
        document_id="policy_a",
        title="Lending Policy",
        source="policy_a.txt",
        source_type="txt",
        content="Fixed rate is 6.49% for Tier 1 credit score 750+. Prepayment penalty is $0."
    )
    doc2 = DocumentRecord(
        document_id="policy_a_copy",
        title="Lending Policy Copy",
        source="policy_a_copy.txt",
        source_type="txt",
        content="Fixed rate is 6.49% for Tier 1 credit score 750+. Prepayment penalty is $0."
    )
    kept, reports = dedup.process_documents([doc1, doc2])
    assert len(kept) == 1
    assert kept[0].document_id == "policy_a"
    assert len(reports) == 1
    assert reports[0]["type"] == "exact_duplicate"

def test_version_lineage_preserved(dedup):
    # Same policy content family with different versions (v1 vs v2)
    doc_v1 = DocumentRecord(
        document_id="policy_v1",
        title="Lending Policy",
        source="policy_v1.txt",
        source_type="txt",
        version="1.0",
        content="Fixed APR is 7.99% for Tier 1 credit scores. Minimum income is $3,000 per month."
    )
    doc_v2 = DocumentRecord(
        document_id="policy_v2",
        title="Lending Policy",
        source="policy_v2.txt",
        source_type="txt",
        version="2.0",
        content="Fixed APR is 6.49% for Tier 1 credit scores. Minimum income is $2,500 per month."
    )
    kept, reports = dedup.process_documents([doc_v1, doc_v2])
    # Both versions must be kept to preserve policy history!
    assert len(kept) == 2
    assert any(r["type"] == "version_variant" for r in reports)
