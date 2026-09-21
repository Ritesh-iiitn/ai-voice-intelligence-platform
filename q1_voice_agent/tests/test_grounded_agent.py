import pytest
from q2_knowledge_base.ingestion.reader import DocumentIngestor
from q2_knowledge_base.chunking.chunker import SemanticSectionChunker
from q2_knowledge_base.embeddings.local import LocalVectorEmbeddingProvider
from q2_knowledge_base.indexing.vector_index import VectorIndex
from q2_knowledge_base.retrieval.bm25 import BM25Retriever
from q2_knowledge_base.retrieval.hybrid import HybridRetriever

from q1_voice_agent.agent.engine import VoiceAgentEngine
from q1_voice_agent.agent.state_machine import CallState

@pytest.fixture(scope="module")
def grounded_engine():
    # Build complete Q2 Knowledge Base
    ingestor = DocumentIngestor()
    chunker = SemanticSectionChunker()

    docs = ingestor.ingest_directory("data/source_documents")
    all_chunks = []
    for d in docs:
        if d.status == "success":
            all_chunks.extend(chunker.chunk_document(d))

    embedder = LocalVectorEmbeddingProvider()
    v_index = VectorIndex(embedding_provider=embedder)
    v_index.build_index(all_chunks)

    bm25 = BM25Retriever()
    bm25.build_index(all_chunks)

    retriever = HybridRetriever(
        vector_index=v_index,
        bm25_retriever=bm25,
        confidence_threshold=0.25
    )

    return VoiceAgentEngine(retriever=retriever)

def test_grounded_prepayment_question(grounded_engine):
    state, _ = grounded_engine.start_call("Michael Scott")
    # Move past greeting
    grounded_engine.process_turn(state, "Yes, speaking.")
    grounded_engine.process_turn(state, "Yes, recording is fine.")
    
    # Customer asks grounded FAQ about prepayment
    out = grounded_engine.process_turn(state, "Can I pay off my loan early without any penalty?")
    assert "$0" in out["response"] or "penalty" in out["response"].lower()
    assert len(out["citations"]) > 0
    assert any("Source:" in c for c in out["citations"])

def test_unsupported_question_triggers_fallback(grounded_engine):
    state, _ = grounded_engine.start_call("Stanley Hudson")
    grounded_engine.process_turn(state, "Yes.")
    grounded_engine.process_turn(state, "Okay.")
    
    # Customer asks about crypto staking
    out = grounded_engine.process_turn(state, "Do you offer crypto-backed collateral loans with Bitcoin staking yields?")
    assert "don't have reliable information" in out["response"].lower()
    assert "specialist" in out["response"].lower() or "representative" in out["response"].lower()

def test_human_escalation_flow(grounded_engine):
    state, _ = grounded_engine.start_call("Pam Beesly")
    grounded_engine.process_turn(state, "Yes, Pam speaking.")
    
    # Customer explicitly requests a human agent
    out = grounded_engine.process_turn(state, "Can I speak to a human representative please?")
    assert state.current_state == CallState.ESCALATION
    assert state.escalation_requested is True
    assert "transferring you directly to a licensed human specialist" in out["response"].lower()
    assert "lead" in out
    assert out["lead"]["qualification"] == "escalated"

def test_complete_cooperative_qualification_call(grounded_engine):
    state, _ = grounded_engine.start_call("Jim Halpert", phone="+1-555-908-1234")
    grounded_engine.process_turn(state, "Yes, this is Jim.")
    grounded_engine.process_turn(state, "Yes, I agree to recording.")
    grounded_engine.process_turn(state, "I want to borrow $30,000 for an auto loan.")
    grounded_engine.process_turn(state, "My monthly take-home income is $6,000.")
    out = grounded_engine.process_turn(state, "My credit score is 780.")
    
    assert state.current_state == CallState.RESULT
    assert state.qualification_status == "qualified"
    assert "Tier 1" in out["response"]
    assert "6.49%" in out["response"]
    assert "lead" in out
    assert out["lead"]["name"] == "Jim Halpert"
