#!/usr/bin/env python3
"""
Full ingestion, cleaning, deduplication, PII protection, chunking, and indexing pipeline.
Builds vector and BM25 indices in data/indices/.
"""
import os
import sys
from pathlib import Path

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from q2_knowledge_base.ingestion.reader import DocumentIngestor
from q2_knowledge_base.cleaning.cleaner import DocumentCleaner
from q2_knowledge_base.pii.redactor import PIIDetectorRedactor
from q2_knowledge_base.deduplication.dedup import Deduplicator
from q2_knowledge_base.chunking.chunker import SemanticSectionChunker
from q2_knowledge_base.embeddings.local import LocalVectorEmbeddingProvider
from q2_knowledge_base.indexing.vector_index import VectorIndex
from q2_knowledge_base.retrieval.bm25 import BM25Retriever

def run_ingestion(source_dir: str = "data/source_documents", index_dir: str = "data/indices"):
    print(f"=== Starting Ingestion Pipeline from {source_dir} ===")
    
    # 1. Ingestion
    ingestor = DocumentIngestor()
    raw_docs = ingestor.ingest_directory(source_dir)
    print(f"Ingested {len(raw_docs)} raw documents.")

    # 2. Cleaning & PII Processing
    cleaner = DocumentCleaner()
    redactor = PIIDetectorRedactor()

    cleaned_docs = []
    for doc in raw_docs:
        if doc.status == "success":
            doc.content = cleaner.clean_text(doc.content)
            # Process and redact PII if present
            doc = redactor.process_document(doc, redact_content=True)
            cleaned_docs.append(doc)
            print(f"  - Cleaned '{doc.title}' (contains_pii={doc.contains_pii}, pii_types={doc.pii_types})")
        else:
            print(f"  ! Skipped '{doc.document_id}' due to status: {doc.status} ({doc.error_message})")

    # 3. Deduplication
    dedup = Deduplicator()
    unique_docs, dedup_reports = dedup.process_documents(cleaned_docs)
    print(f"Retained {len(unique_docs)} documents after deduplication check.")
    for report in dedup_reports:
        print(f"    [DEDUP REPORT] {report['type']}: {report['doc_id']} -> {report.get('reason')}")

    # 4. Semantic Chunking
    chunker = SemanticSectionChunker()
    all_chunks = []
    for doc in unique_docs:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)
        print(f"  - Chunked '{doc.document_id}' -> {len(chunks)} semantic chunks")

    print(f"Total semantic chunks generated: {len(all_chunks)}")

    # 5. Indexing: Vector & BM25
    embedding_provider = LocalVectorEmbeddingProvider()
    vector_index = VectorIndex(embedding_provider=embedding_provider)
    vector_index.build_index(all_chunks)
    vector_index.save(index_dir)

    bm25 = BM25Retriever()
    bm25.build_index(all_chunks)

    print(f"Indices saved successfully to {index_dir}/")
    return vector_index, bm25, all_chunks

if __name__ == "__main__":
    run_ingestion()
