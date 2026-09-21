# Production-Grade Voice AI & Real-Time Telemetry Platform

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-78%20Passed-brightgreen.svg)](tests/)
[![Sub-Second SLA](https://img.shields.io/badge/RealTime%20P95-36.45ms-success.svg)](docs/latency/Q4_LATENCY_REPORT.md)

An enterprise-ready, grounded Voice AI platform for **Auto & Personal Lending with Embedded Loan Protection Insurance**. This platform demonstrates full end-to-end implementations for:
* **Q1: Grounded Conversational Voice Agent**: State machine with strict underwriting rules, conflict clarification, and human escalation dispatch to CRM.
* **Q2: Enterprise Knowledge Base (RAG)**: Multi-format ingestion (PDF, HTML, CSV, TXT, DOCX), automated PII masking, semantic section chunking, and dual-retrieval (Dense Cosine + Okapi BM25) with Reciprocal Rank Fusion (RRF).
* **Q3: Multilingual Localization**: Native regional voice agents for the Philippines (Taglish + insurance lexicon) and Indonesia (Bahasa + consumer credit terms + Javanese dialect), backed by dynamic language routing.
* **Q4: Real-Time Sub-Second Insights & Nudges**: Sliding-window audio streaming, live transcript buffering, automated signal detection (`missed_cross_sell`, `compliance_gap`, `rising_frustration`, `payment_difficulty`), 20-second cooldown suppression engine, and an interactive WebSocket supervisor cockpit.

---

## ⚡ Quick Start (One-Minute Run)

### 1. Environment Setup
```bash
# Clone and enter directory
git checkout assessment-build

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run All Automated Test Suites
```bash
pytest -v
# 78 passed in 0.79s
```

### 3. Run Benchmark Evaluations (Q2, Q3, Q4)
```bash
# Evaluate Knowledge Base Hybrid Retrieval (Q2)
python scripts/evaluate_retrieval.py

# Evaluate Multilingual Localization (Q3)
python scripts/evaluate_multilingual.py

# Evaluate Real-Time Telemetry & Nudge Latency + False Positives (Q4)
python scripts/evaluate_realtime.py
```

### 4. Launch the Live API & Supervisor Cockpit
```bash
uvicorn apps.api.main:app --reload --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your web browser to access the live dashboard with interactive scenario simulation!

---

## 🏛️ Platform Architecture Overview

```
                        ┌──────────────────────────────────────────────┐
                        │   Inbound Telephony / WebRTC Stream / SIP    │
                        └──────────────────────┬───────────────────────┘
                                               │
                                               ▼
                        ┌──────────────────────────────────────────────┐
                        │        FastAPI Gateway & WebSocket Hub       │
                        │           (apps/api/main.py:8000)            │
                        └──────────────┬───────────────┬───────────────┘
                                       │               │
                 ┌─────────────────────┘               └─────────────────────┐
                 ▼                                                           ▼
┌──────────────────────────────────────┐                   ┌──────────────────────────────────────┐
│       Q1: Grounded Voice Agent       │                   │    Q4: Sub-Second Telemetry Pipeline │
│  - State Machine (Greeting -> Result)│                   │  - 250ms Audio Chunk Ring Buffer     │
│  - Conflict & Discrepancy Validator  │                   │  - Streaming ASR (Mock / Deepgram)   │
│  - Underwriting Rules (DTI, Tiers)   │                   │  - Signal Detector (4 Categories)    │
│  - Escalation & Mock CRM Dispatch    │                   │  - Nudge Engine (20s Cooldowns)      │
└──────────────────┬───────────────────┘                   └──────────────────┬───────────────────┘
                   │                                                          │
                   ▼                                                          ▼
┌──────────────────────────────────────┐                   ┌──────────────────────────────────────┐
│       Q2: Knowledge Base (RAG)       │                   │       Live Supervisor Cockpit        │
│  - Multi-Format Parser (PDF/CSV/HTML)│                   │  - Real-time scrolling transcript    │
│  - PII Redactor (SSN, TIN, NIK)      │                   │  - Instant signal badge trigger      │
│  - Semantic Section Chunker          │                   │  - Actionable nudge script cards     │
│  - Dense Cosine + Okapi BM25 (RRF)   │                   │  - Sub-second latency telemetry bar  │
└──────────────────┬───────────────────┘                   └──────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│     Q3: Multilingual Localization    │
│  - Dynamic Language & Market Router  │
│  - Philippines Taglish Bot (PHP)     │
│  - Indonesia Bahasa Bot (IDR / Java) │
└──────────────────────────────────────┘
```

---

## 📦 Detailed Module Highlights

### 1. Q1 Grounded Voice Agent (`q1_voice_agent/`)
* **Conversational State Machine**: Strict step transitions (`GREETING` $\to$ `CONSENT` $\to$ `COLLECT_DETAILS` $\to$ `QUALIFICATION` $\to$ `RESULT` / `ESCALATION`).
* **Entity Extraction & Conflict Resolution**: Automatically identifies discrepancies (e.g. initial stated income $\$8,000$ vs later paystub $\$3,000$; credit score 750 vs reported 580) and triggers a polite clarification loop.
* **Underwriting Engine**: Real lending logic applying $45\%$ maximum DTI, minimum $\$2,500$ monthly income, and tiered interest rate pricing (Tier 1: $6.49\%$, Tier 2: $8.99\%$, Tier 3: $12.49\%$, Tier 4: Ineligible).
* **CRM Lead Generation**: Automatically creates mock CRM lead entries with qualification results or human escalation dispatch payloads.

### 2. Q2 Enterprise Knowledge Base (`q2_knowledge_base/`)
* **Multi-Format Ingestion**: Ingests PDF (`pypdf`), HTML (`BeautifulSoup4`), CSV, and TXT from `data/source_documents/` with malformed file handling.
* **Automated PII Protection**: Token-based redaction for US SSN, Indian PAN/Aadhaar, Philippine TIN, Indonesian NIK, emails, and bank accounts prior to chunking.
* **Section-Aware Chunker**: Respects hierarchical markdown headers and policy clauses while preserving document title and version tags.
* **Hybrid Retrieval Engine**:
  * **Dense Semantic Search**: Cosine similarity over L2-normalized embeddings.
  * **Keyword Search**: Okapi BM25 inverted index with English stop-word filtering.
  * **Reciprocal Rank Fusion**: Re-weights rank fusion with candidate cosine/BM25 scores and enforces a $0.25$ confidence cutoff to eliminate hallucinations on out-of-scope queries (e.g. crypto collateral).
* **Evaluation Benchmark**: MRR = `0.917`, Precision@3 = `100%`, 0 incorrect answers.

### 3. Q3 Multilingual Localization (`q3_multilingual/`)
* **Philippines Market (`PH`)**:
  * Taglish conversational register (`"Opo, i-check po natin ang inyong loan eligibility..."`).
  * Currency parser: Handles `PHP`, `₱`, `pesos`, and shorthand `15k` $\to 15,000$.
  * Insurance lexicon: *premium, beneficiary, rider, lapse, coverage*.
* **Indonesia Market (`ID`)**:
  * Bahasa Indonesia with polite formal markers (`"Bapak/Ibu"`) and regional Javanese accent handling (`"Nyuwun sewu mas..."`).
  * Currency parser: Handles `IDR`, `Rp`, `rupiah`, and `juta` multipliers (`10jt` $\to 10,000,000$).
  * Consumer credit terms: *cicilan, tenor, denda, DP (down payment), angsuran*.
* **Language Router**: Automatically detects language register and dialect markers to route callers to the localized engine without unexpected fallback to English.

### 4. Q4 Real-Time Telemetry & Agent Nudges (`q4_realtime/`)
* **Sliding-Window Audio Buffer**: Manages 250ms audio chunks in a thread-safe circular buffer with 60-second retention limit to prevent memory leaks.
* **Four Conversational Business Signals**:
  1. `missed_cross_sell`: Triggers when customer mentions a second vehicle, spouse car, or payment protection rider.
  2. `compliance_gap`: Triggers when agent quotes concrete interest rates without APR disclosure, promises guaranteed approval, or requests PII without recording notice.
  3. `rising_frustration`: Detects severe complaints, repetition fatigue, and human transfer demands.
  4. `payment_difficulty`: Detects job loss, reduced hours, medical emergencies, or requests for installment extensions.
* **Intelligent Nudge Engine**:
  * Minimum confidence threshold: $< 0.70$ suppressed.
  * Cooldown timer: 20-second suppression per signal type to prevent visual noise.
  * Deduplication: Grouped by topic and capped at 2 repeats per call.
  * Prioritization: `CRITICAL` (pulsing red for compliance violations), `HIGH` (payment hardship, missing APR), `MEDIUM` (cross-sell discounts).
  * Actionable guidance: Verbatim scripts with a 1-click "Copy Script" button.

---

## 📊 Empirical Evaluation Results

| Benchmark Suite | Test Cases | Primary Metric | Result | Target / SLA | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Q2 Knowledge Base Retrieval** | 6 policy queries | Mean Reciprocal Rank (MRR) | **`0.917`** | $\ge 0.80$ | ✅ PASS |
| **Q2 Retrieval Precision** | 6 policy queries | Precision@3 | **`100.0%`** | $\ge 85.0\%$ | ✅ PASS |
| **Q1 Voice Agent Scenarios** | 5 dialogues | Turn Completion & Escalation | **`100.0%`** | $100.0\%$ | ✅ PASS |
| **Q3 Multilingual Accuracy** | 10 regional turns | Dialect & Terminology Retention | **`100.0%`** | $\ge 90.0\%$ | ✅ PASS |
| **Q4 Real-Time End-to-End Latency** | 100 stream frames | P95 Pipeline Latency | **`36.45 ms`** | $< 1,000 \text{ ms}$ | ✅ PASS (96% Margin) |
| **Q4 Signal Detection Precision** | 18 benchmark cases | Overall Precision | **`100.0%`** | $\ge 90.0\%$ | ✅ PASS |
| **Q4 Signal False Positive Rate** | 18 benchmark cases | False Positive Rate | **`0.0%`** | $< 5.0\%$ | ✅ PASS |

---

## 🚀 Scaling Analysis: 1,000 $\to$ 10,000 Concurrent Calls (10x Volume)

When scaling an enterprise voice AI platform from $1,000$ to $10,000$ active concurrent calls, the engineering architecture must transition from in-memory single-process workers to a distributed, sharded, horizontally scalable event topology.

### 1. Throughput & Network Sizing
* **Audio Chunk Rate**: $10,000 \text{ calls} \times 4 \text{ chunks/sec (250ms chunks)} = 40,000 \text{ chunks/second}$.
* **Audio Data Bandwidth**:
  $$\text{Per Stream} = 16 \text{ kHz} \times 16 \text{ bit PCM} = 256 \text{ kbps} = 32 \text{ kB/s}$$
  $$10,000 \text{ concurrent streams} = 320 \text{ MB/s} = 2.56 \text{ Gbps network ingress}$$
* **Architecture Strategy**:
  * Offload SSL termination and SIP/WebRTC media proxying to edge SBCs (Session Border Controllers) or LiveKit/Envoy clusters.
  * Ingest audio frames into a distributed messaging queue (e.g. **Apache Kafka** or **AWS Kinesis**) partitioned by `call_id`.

### 2. ASR & GPU Provisioning
* High-concurrency streaming speech recognition cannot be hosted on single CPU nodes.
* **ASR Worker Cluster**:
  * Deploy streaming models (e.g., Deepgram on-prem or Whisper-Streaming on Triton Inference Server).
  * With a Real-Time Factor (RTF) of $0.05$ on NVIDIA A10G / L4 GPUs, one GPU can comfortably process $15$ to $20$ concurrent speech streams without queuing delay.
  * To support $10,000$ concurrent streams, provision a Kubernetes cluster of approximately **500 GPU worker pods** auto-scaled via KEDA based on audio buffer lag.

### 3. State Management & In-Memory Sharding
* Currently, audio buffers and call state machines reside in Python memory.
* **Distributed Sharding**:
  * Use **Redis Cluster** (or DragonFly) with Redis Streams for temporary audio chunk buffering (TTL = 120 seconds).
  * Maintain dialog session state in Redis with write-through replication to PostgreSQL / DynamoDB for completed call records.
  * Consistent hashing on `call_id` ensures all chunks from a given call route to the same worker instance, preserving CPU cache locality.

### 4. Vector & Retrieval Scaling
* Q2 utilizes in-memory NumPy/TF-IDF.
* At $10,000$ calls, grounding queries can peak at $2,000 \text{ QPS}$.
* **Production Retrieval Cluster**:
  * Migrate dense vectors to a dedicated vector database (**Qdrant** or **Milvus**) with HNSW indexing and memory-mapped files.
  * Keep Okapi BM25 on **Elasticsearch / OpenSearch** with read replicas.
  * Implement an aggressive LRU Redis cache for frequently asked policy queries ($>65\%$ cache hit rate for common FAQ queries).

---

## 🗺️ Production Roadmap & Hardening

1. **Phase 1: Telephony Integration**
   * Integrate FreeSWITCH / Asterisk / Twilio Media Streams over WebSocket.
   * Add bi-directional SIP INVITE handling and WebRTC client SDK.
2. **Phase 2: Live LLM Fine-Tuning**
   * Fine-tune a compact 8B parameter model (e.g. Llama 3 / Mistral) on regional loan objection handling and compliance disclosures.
   * Quantize via vLLM / TensorRT-LLM for $<250$ms time-to-first-token.
3. **Phase 3: Advanced Observability & Telemetry**
   * Export OpenTelemetry spans for every chunk: `audio_ingest` $\to$ `asr_decode` $\to$ `signal_detect` $\to$ `nudge_emit`.
   * Real-time Grafana dashboards monitoring P50/P95/P99 latencies, talk-ratios, and compliance violation heatmaps.
4. **Phase 4: Regulatory Auditing & Zero-PII Vault**
   * Implement automated PII anonymization before saving call recordings to S3/GCS.
   * Immutable cryptographic audit trail for compliance disclosures and customer consent records.

---

## 🤝 Verification & Contributing

All code is thoroughly covered by automated test suites and evaluation harnesses:
```bash
# Run complete test suite (78 tests)
pytest

# Inspect requirements traceability matrix
cat docs/REQUIREMENTS_TRACEABILITY.md

# Inspect architecture specifications and diagrams
cat docs/architecture/SYSTEM_ARCHITECTURE.md
```
