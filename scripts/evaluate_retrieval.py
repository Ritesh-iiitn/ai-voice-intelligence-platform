#!/usr/bin/env python3
"""
Retrieval evaluation suite benchmarking the Knowledge Base on 6 representative queries.
Computes Precision@K, Mean Reciprocal Rank (MRR), and writes docs/evaluation/q2_retrieval_results.md.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from q2_knowledge_base.ingestion.reader import DocumentIngestor
from q2_knowledge_base.cleaning.cleaner import DocumentCleaner
from q2_knowledge_base.chunking.chunker import SemanticSectionChunker
from q2_knowledge_base.embeddings.local import LocalVectorEmbeddingProvider
from q2_knowledge_base.indexing.vector_index import VectorIndex
from q2_knowledge_base.retrieval.bm25 import BM25Retriever
from q2_knowledge_base.retrieval.hybrid import HybridRetriever
from q2_knowledge_base.retrieval.citation import CitationFormatter

EVALUATION_BENCHMARK = [
    {
        "id": "Q2-EVAL-01",
        "question": "What is the fixed APR interest rate for someone with a credit score of 760?",
        "expected_info": "Tier 1 APR is 6.49% for credit scores 750+",
        "expected_sources": ["credit_lending_policy_v2.txt", "credit_lending_policy_v2.pdf", "faq_and_objections.csv"],
        "expected_keywords": ["6.49%", "Tier 1", "750+"]
    },
    {
        "id": "Q2-EVAL-02",
        "question": "Will I be penalized if I pay off my auto loan balance early?",
        "expected_info": "$0 prepayment penalty; borrowers may settle full balance anytime without penalty",
        "expected_sources": ["credit_lending_policy_v2.txt", "faq_and_objections.csv"],
        "expected_keywords": ["$0", "prepayment"]
    },
    {
        "id": "Q2-EVAL-03",
        "question": "What is the minimum monthly net income required to be eligible?",
        "expected_info": "Minimum net monthly income of $2,500 supported by pay slips or bank statements",
        "expected_sources": ["credit_lending_policy_v2.txt", "credit_lending_policy_v2.pdf", "faq_and_objections.csv"],
        "expected_keywords": ["$2,500", "income"]
    },
    {
        "id": "Q2-EVAL-04",
        "question": "What protection is provided if I lose my job unexpectedly?",
        "expected_info": "Involuntary Unemployment Rider covers up to 6 monthly installments (up to $3,000/month)",
        "expected_sources": ["insurance_protection_riders.html", "faq_and_objections.csv"],
        "expected_keywords": ["Involuntary Unemployment", "installments"]
    },
    {
        "id": "Q2-EVAL-05",
        "question": "Is there a discount for protecting multiple household vehicles?",
        "expected_info": "Multi-Vehicle Household Bundle provides 15% discount on combined protection premiums",
        "expected_sources": ["insurance_protection_riders.html", "faq_and_objections.csv"],
        "expected_keywords": ["15% discount", "Multi-Vehicle"]
    },
    {
        "id": "Q2-EVAL-06",
        "question": "Do you offer crypto-backed collateral loans with Bitcoin staking yields?",
        "expected_info": "Out of scope. No policy records exist for cryptocurrency or staking.",
        "expected_sources": ["NONE"],
        "expected_keywords": []
    }
]

def evaluate_knowledge_base():
    print("=== Running Knowledge Base Retrieval Evaluation Suite ===")
    
    # 1. Ingest & Chunk documents
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
    vector_idx = VectorIndex(embedding_provider=embedder)
    vector_idx.build_index(all_chunks)

    bm25 = BM25Retriever()
    bm25.build_index(all_chunks)

    retriever = HybridRetriever(
        vector_index=vector_idx,
        bm25_retriever=bm25,
        confidence_threshold=0.30
    )

    eval_results = []
    reciprocal_ranks = []
    precision_at_3_scores = []

    for item in EVALUATION_BENCHMARK:
        qid = item["id"]
        question = item["question"]
        expected_sources = item["expected_sources"]
        expected_kw = item["expected_keywords"]

        # Run hybrid retrieval
        retrieved = retriever.retrieve(question, top_k=3, apply_threshold=True)

        # Evaluate Out of scope query
        if "NONE" in expected_sources:
            # Query has no relevant facts in KB
            has_unsupported_facts = any(any(kw.lower() in r.content.lower() for kw in ["bitcoin", "crypto", "staking"]) for r in retrieved)
            if not has_unsupported_facts:
                verdict = "correct"
                reciprocal_rank = 1.0
                p_at_3 = 1.0
                explanation = "Query has no facts in KB; zero hallucinated facts retrieved, enabling safe fallback."
            else:
                verdict = "incorrect"
                reciprocal_rank = 0.0
                p_at_3 = 0.0
                explanation = "Unexpectedly retrieved cryptocurrency claims."
        else:
            # Check ranks of retrieved chunks
            found_rank = None
            relevant_count = 0

            for r_idx, res in enumerate(retrieved, start=1):
                src_match = any(es.lower() in res.source.lower() for es in expected_sources)
                kw_match = any(kw.lower() in res.content.lower() for kw in expected_kw)

                if src_match and kw_match:
                    relevant_count += 1
                    if found_rank is None:
                        found_rank = r_idx

            if found_rank == 1:
                verdict = "correct"
                reciprocal_rank = 1.0
                explanation = f"Top-ranked chunk directly matched verified policy source and facts."
            elif found_rank is not None:
                verdict = "partially_correct"
                reciprocal_rank = 1.0 / found_rank
                explanation = f"Relevant information retrieved at rank #{found_rank}."
            else:
                verdict = "incorrect"
                reciprocal_rank = 0.0
                explanation = "Failed to retrieve the expected policy rule in top 3 results."

            p_at_3 = relevant_count / 3.0

        reciprocal_ranks.append(reciprocal_rank)
        precision_at_3_scores.append(p_at_3)

        eval_results.append({
            "id": qid,
            "question": question,
            "expected_info": item["expected_info"],
            "retrieved_records": [
                {
                    "chunk_id": r.chunk_id,
                    "source": Path(r.source).name,
                    "section": r.section,
                    "version": r.version,
                    "score": r.score,
                    "type": r.retrieval_type,
                    "snippet": r.content[:140].replace("\n", " ") + "..."
                }
                for r in retrieved
            ],
            "verdict": verdict,
            "reciprocal_rank": reciprocal_rank,
            "precision_at_3": round(p_at_3, 3),
            "explanation": explanation
        })

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    mean_p_at_3 = sum(precision_at_3_scores) / len(precision_at_3_scores) if precision_at_3_scores else 0.0

    print(f"Evaluation Finished: MRR={mrr:.3f}, Mean Precision@3={mean_p_at_3:.3f}")

    # Generate Markdown Report in docs/evaluation/q2_retrieval_results.md
    generate_markdown_report(eval_results, mrr, mean_p_at_3)
    return eval_results, mrr, mean_p_at_3

def generate_markdown_report(results: List[Dict[str, Any]], mrr: float, mean_p3: float):
    out_path = Path("docs/evaluation/q2_retrieval_results.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    md = []
    md.append("# Question 2: Knowledge Base Retrieval Evaluation Report\n")
    md.append(f"**Evaluation Date:** 2026-09-22\n")
    md.append(f"**Pipeline:** Multi-format Ingestion -> Cleaning & PII Masking -> Semantic Chunking -> Local Dense TF-IDF + BM25 Hybrid Retrieval\n")
    md.append(f"**Summary Metrics:**\n")
    md.append(f"- **Mean Reciprocal Rank (MRR):** `{mrr:.3f}`")
    md.append(f"- **Mean Precision@3:** `{mean_p3:.3f}`")
    md.append(f"- **Total Benchmark Queries:** `{len(results)}`\n")

    correct_count = sum(1 for r in results if r["verdict"] == "correct")
    partial_count = sum(1 for r in results if r["verdict"] == "partially_correct")
    incorrect_count = sum(1 for r in results if r["verdict"] == "incorrect")

    md.append(f"| Metric | Value |")
    md.append(f"| :--- | :--- |")
    md.append(f"| Correct | {correct_count} ({correct_count/len(results)*100:.1f}%) |")
    md.append(f"| Partially Correct | {partial_count} ({partial_count/len(results)*100:.1f}%) |")
    md.append(f"| Incorrect | {incorrect_count} ({incorrect_count/len(results)*100:.1f}%) |")
    md.append(f"| MRR Score | {mrr:.3f} |")
    md.append(f"| Mean Precision@3 | {mean_p3:.3f} |\n")

    md.append("## Detailed Query Benchmark Results\n")

    for r in results:
        md.append(f"### Query `{r['id']}`: {r['question']}\n")
        md.append(f"- **Expected Information:** {r['expected_info']}")
        md.append(f"- **Verdict:** `{r['verdict'].upper()}` (RR: `{r['reciprocal_rank']}`, P@3: `{r['precision_at_3']}`)")
        md.append(f"- **Explanation:** {r['explanation']}\n")

        if r["retrieved_records"]:
            md.append("#### Retrieved Top Records:")
            for i, rec in enumerate(r["retrieved_records"], start=1):
                md.append(
                    f"{i}. **{rec['chunk_id']}** (Score: `{rec['score']}`, Mode: `{rec['type']}`)\n"
                    f"   - Citation: `[Source: {rec['source']} | Section: {rec['section']} | Version: {rec['version']}]`\n"
                    f"   - Content: *\"{rec['snippet']}\"*"
                )
        else:
            md.append("*No records passed the confidence threshold (correctly filtered out-of-scope inquiry).*")

        md.append("\n---\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Report written to {out_path}")

if __name__ == "__main__":
    evaluate_knowledge_base()
