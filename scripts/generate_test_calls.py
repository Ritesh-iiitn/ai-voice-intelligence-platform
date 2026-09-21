#!/usr/bin/env python3
"""
Test call generator executing 5 comprehensive voice call scenarios:
1. Cooperative Customer
2. Customer Objection Handling
3. Incomplete & Conflicting Details
4. Out-of-Scope / Unsupported Question
5. Explicit Human Escalation

Generates structured outcome payloads, transcripts, recordings, and writes docs/evaluation/q1_test_results.md.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from q2_knowledge_base.ingestion.reader import DocumentIngestor
from q2_knowledge_base.cleaning.cleaner import DocumentCleaner
from q2_knowledge_base.chunking.chunker import SemanticSectionChunker
from q2_knowledge_base.embeddings.local import LocalVectorEmbeddingProvider
from q2_knowledge_base.indexing.vector_index import VectorIndex
from q2_knowledge_base.retrieval.bm25 import BM25Retriever
from q2_knowledge_base.retrieval.hybrid import HybridRetriever

from q1_voice_agent.agent.engine import VoiceAgentEngine
from q1_voice_agent.agent.state_machine import CallState
from q1_voice_agent.providers.mock import MockVoiceProvider

def setup_grounded_engine() -> VoiceAgentEngine:
    ingestor = DocumentIngestor()
    cleaner = DocumentCleaner()
    chunker = SemanticSectionChunker()

    docs = ingestor.ingest_directory("data/source_documents")
    all_chunks = []
    for d in docs:
        if d.status == "success":
            d.content = cleaner.clean_text(d.content)
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

SCENARIOS = [
    {
        "id": "SCENARIO-01",
        "name": "Cooperative Customer (Pre-approval)",
        "customer": "Jim Halpert",
        "phone": "+1-555-019-2831",
        "utterances": [
            "Yes, this is Jim speaking.",
            "Yes, recording is fine, go ahead.",
            "I am looking for an auto loan of about $30,000.",
            "My monthly net income is approximately $6,000.",
            "My credit score is 780."
        ]
    },
    {
        "id": "SCENARIO-02",
        "name": "Customer Objection (Rate too high)",
        "customer": "Dwight Schrute",
        "phone": "+1-555-014-9922",
        "utterances": [
            "Yes, Dwight Schrute here.",
            "Yes, you have consent.",
            "I need a $40,000 vehicle loan, but the interest rate feels a bit too high for me.",
            "My monthly income is $5,500.",
            "My credit score is 725."
        ]
    },
    {
        "id": "SCENARIO-03",
        "name": "Incomplete & Conflicting Financial Details",
        "customer": "Andy Bernard",
        "phone": "+1-555-018-3341",
        "utterances": [
            "Speaking! Andy here.",
            "Sure, record away.",
            "I need around $20,000.",
            "My take home is $1,800 a month.",
            "Actually sorry, my take home is $5,200 including commissions.",
            "My credit score is 690."
        ]
    },
    {
        "id": "SCENARIO-04",
        "name": "Out-of-Scope / Unsupported Question",
        "customer": "Ryan Howard",
        "phone": "+1-555-017-7711",
        "utterances": [
            "Yes, Ryan.",
            "Fine.",
            "Do you offer crypto-backed collateral loans with Bitcoin staking yields?",
            "Okay, what about regular auto loans? I need $15,000.",
            "Income is $3,800.",
            "Credit score 710."
        ]
    },
    {
        "id": "SCENARIO-05",
        "name": "Explicit Human Escalation",
        "customer": "Kelly Kapoor",
        "phone": "+1-555-012-4455",
        "utterances": [
            "Yes, Kelly here!",
            "Can I speak to a human representative right now please? I don't want to talk to an automated system."
        ]
    }
]

def run_all_test_calls():
    print("=== Generating Test Calls and Transcripts ===")
    engine = setup_grounded_engine()
    voice_prov = MockVoiceProvider()

    transcripts_dir = Path("q1_voice_agent/transcripts")
    recordings_dir = Path("q1_voice_agent/recordings")
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    recordings_dir.mkdir(parents=True, exist_ok=True)

    results_summary = []

    for sc in SCENARIOS:
        print(f"\n--- Running {sc['id']}: {sc['name']} ---")
        state, initial_greeting = engine.start_call(sc["customer"], sc["phone"])

        turn_logs = [{"speaker": "Agent", "utterance": initial_greeting}]
        last_turn_data = {}

        for user_utt in sc["utterances"]:
            print(f"Customer: {user_utt}")
            turn_logs.append({"speaker": "Customer", "utterance": user_utt})
            turn_res = engine.process_turn(state, user_utt)
            last_turn_data = turn_res
            agent_resp = turn_res["response"]
            print(f"Agent: {agent_resp}")
            turn_logs.append({
                "speaker": "Agent",
                "utterance": agent_resp,
                "state": turn_res["state"].value,
                "citations": turn_res.get("citations", [])
            })

        # Save audio recording
        sample_audio = voice_prov.synthesize_speech(" ".join([t["utterance"] for t in turn_logs if t["speaker"] == "Agent"]))
        audio_filename = f"{sc['id'].lower()}.wav"
        with open(recordings_dir / audio_filename, "wb") as f:
            f.write(sample_audio)

        # Save structured transcript
        scenario_record = {
            "scenario_id": sc["id"],
            "scenario_name": sc["name"],
            "customer_name": sc["customer"],
            "phone": sc["phone"],
            "final_state": state.current_state.value,
            "qualification_status": state.qualification_status,
            "conflicts_detected": state.conflicts_detected,
            "escalation_requested": state.escalation_requested,
            "lead": last_turn_data.get("lead"),
            "citations_used": state.cited_sources,
            "recording_file": f"recordings/{audio_filename}",
            "dialogue_history": turn_logs
        }

        json_path = transcripts_dir / f"{sc['id'].lower()}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scenario_record, f, indent=2)

        results_summary.append(scenario_record)

    # Write evaluation report
    write_q1_evaluation_report(results_summary)
    print("\nTest calls and evaluation report successfully generated!")
    return results_summary

def write_q1_evaluation_report(results: List[Dict[str, Any]]):
    out_path = Path("docs/evaluation/q1_test_results.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    md = []
    md.append("# Question 1: Knowledge-Grounded Voice Agent Test Results\n")
    md.append("**Evaluation Date:** 2026-09-22\n")
    md.append("This document records the evaluation of 5 end-to-end test call scenarios testing grounding, underwriting rules, conflict resolution, unsupported question handling, and human escalation.\n")
    md.append("| Scenario ID | Scenario Name | Customer | Final State | Outcome | Citations Count | Recording |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for r in results:
        status = r["qualification_status"] or ("Escalated" if r["escalation_requested"] else r["final_state"])
        c_count = len(r["citations_used"])
        rec = r["recording_file"]
        md.append(f"| `{r['scenario_id']}` | {r['scenario_name']} | {r['customer_name']} | `{r['final_state']}` | **{status}** | `{c_count}` | [`{rec}`]({rec}) |")

    md.append("\n## Detailed Scenario Breakdown\n")

    for r in results:
        md.append(f"### {r['scenario_id']}: {r['scenario_name']}\n")
        md.append(f"- **Customer:** {r['customer_name']} ({r['phone']})")
        md.append(f"- **Final State:** `{r['final_state']}`")
        md.append(f"- **Qualification Status:** `{r['qualification_status']}`")
        md.append(f"- **Conflicts Detected:** `{r['conflicts_detected']}`")
        md.append(f"- **Escalation Triggered:** `{r['escalation_requested']}`")
        if r["lead"]:
            md.append(f"- **Created CRM Lead:** `{r['lead'].get('lead_id')}` (Action: `{r['lead'].get('next_action')}`)\n")

        if r["citations_used"]:
            md.append("**Grounded Citations Used in Call:**")
            for c in r["citations_used"]:
                md.append(f"- `{c}`")
            md.append("")

        md.append("#### Dialogue Transcript:")
        for turn in r["dialogue_history"]:
            md.append(f"- **{turn['speaker']}:** {turn['utterance']}")

        md.append("\n---\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

if __name__ == "__main__":
    run_all_test_calls()
