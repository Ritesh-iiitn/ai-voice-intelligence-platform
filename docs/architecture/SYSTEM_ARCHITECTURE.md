# System Architecture & Technical Specifications

This document outlines the end-to-end software architecture, component relationships, data flows, and state machines for the **Production-Oriented Voice AI & Real-Time Telemetry Platform**.

---

## 1. High-Level Platform Topology

```mermaid
flowchart TD
    subgraph Clients["Edge & Inbound Telephony"]
        PSTN["SIP / PSTN Caller"]
        Browser["Agent Browser / WebRTC"]
    end

    subgraph Gateway["FastAPI Streaming & Telemetry Gateway"]
        API["FastAPI App (apps/api/main.py)"]
        WS["WebSocket Server (/ws/calls/{id})"]
        Buffer["Audio & Transcript Ring Buffers"]
    end

    subgraph Q1["Q1: Grounded Voice Agent"]
        SM["Dialog State Machine"]
        Rules["Underwriting Rules Engine"]
        Validator["Conflict & Discrepancy Validator"]
        Escalation["Escalation & CRM Dispatch"]
    end

    subgraph Q2["Q2: Enterprise Knowledge Base"]
        Ingest["Multi-Format Ingestion (PDF, HTML, CSV, TXT)"]
        PII["PII Detection & Token Masking"]
        Chunker["Semantic Section Chunker"]
        Dense["Dense Cosine Vector Index"]
        BM25["Okapi BM25 Keyword Retriever"]
        RRF["Reciprocal Rank Fusion (RRF)"]
    end

    subgraph Q3["Q3: Multilingual Localization"]
        Router["Language & Market Router"]
        PHTaglish["Philippines Taglish Bot (PHP, Insurance)"]
        IDBahasa["Indonesia Bahasa Bot (IDR, Credit Terms)"]
    end

    subgraph Q4["Q4: Real-Time Insights & Nudges"]
        StreamASR["Streaming ASR Decoder (250ms chunks)"]
        Signals["Signal Detector (4 Categories)"]
        Nudges["Nudge Engine (Cooldowns & Suppression)"]
    end

    subgraph Storage["External Systems & Dashboards"]
        CRM["Mock CRM / Core Banking"]
        Dashboard["Live Supervisor Cockpit (HTML5/WS)"]
    end

    PSTN --> Gateway
    Browser --> Gateway
    Gateway --> Buffer
    Buffer --> StreamASR
    StreamASR --> Signals
    Signals --> Nudges
    Nudges --> WS
    WS --> Dashboard

    Gateway --> Router
    Router --> SM
    Router --> PHTaglish
    Router --> IDBahasa

    SM --> Q2
    Q2 --> RRF
    RRF --> SM
    SM --> Rules
    Rules --> Validator
    Validator --> Escalation
    Escalation --> CRM
```

---

## 2. Q2 Knowledge Base: Ingestion, Indexing, and Grounded Retrieval

The Knowledge Base is designed to ensure zero hallucinations and deterministic policy retrieval across credit lending, loan terms, and insurance coverage.

```mermaid
flowchart LR
    subgraph Ingestion["1. Ingestion Pipeline"]
        RawDocs["Raw Source Documents (PDF, HTML, CSV, TXT, DOCX)"] --> DocReader["DocumentIngestor"]
        DocReader --> Cleaner["DocumentCleaner (HTML strip, Unicode norm)"]
        Cleaner --> PIIRedact["PIIRedactor (SSN, Phone, Email, TIN, NIK)"]
        PIIRedact --> Dedup["Exact Hash & Jaccard Deduplication"]
    end

    subgraph Indexing["2. Chunking & Dual-Indexing"]
        Dedup --> Chunker["SemanticSectionChunker (Preserves Lineage & Hierarchy)"]
        Chunker --> DenseIdx["Dense Vector Index (TF-IDF / Normalized Vectors)"]
        Chunker --> BM25Idx["Okapi BM25 Inverted Index (Stopword filtered)"]
    end

    subgraph Retrieval["3. Hybrid Retrieval & Grounding"]
        Query["User Utterance / Query"] --> DenseIdx
        Query --> BM25Idx
        DenseIdx --> CandidateA["Semantic Matches (Cosine)"]
        BM25Idx --> CandidateB["Exact Keyword Matches"]
        CandidateA --> Fusion["Reciprocal Rank Fusion (RRF)"]
        CandidateB --> Fusion
        Fusion --> Threshold["Confidence Threshold Filter (score >= 0.25)"]
        Threshold --> Citation["CitationFormatter (Source, Section, Version)"]
    end
```

### Key Knowledge Base Invariants:
1. **Document Lineage**: Chunks preserve `document_id`, source filename, section title, and version string (`v1.0`, `v2.0`).
2. **PII Masking**: National identity numbers (US SSN, India PAN/Aadhaar, PH TIN, ID NIK) and financial account numbers are sanitized prior to indexing using replacement tokens (`[REDACTED_SSN]`, `[REDACTED_NIK]`).
3. **Dual Hybrid Ranking**: RRF score calculation:
   $$RRF(d) = \sum_{m \in \{dense, bm25\}} \frac{w_m}{k + \text{rank}_m(d)}$$
   Candidate scores are re-weighted with underlying similarity metrics to ensure queries with zero lexical overlap don't artificially score high.

---

## 3. Q1 Grounded Voice Agent: State Machine & Conflict Resolution

```mermaid
stateDiagram-v2
    [*] --> GREETING: Call Initialized
    GREETING --> CONSENT: Disclose Call Recording
    CONSENT --> COLLECT_DETAILS: Consent Granted
    CONSENT --> ESCALATION: Consent Denied / Explicit Refusal

    COLLECT_DETAILS --> COLLECT_DETAILS: Extract Entity (Income, Loan, Credit Score)
    COLLECT_DETAILS --> CLARIFICATION: Conflict Detected (e.g. Income $8k vs $3k, Score 750 vs 580)
    CLARIFICATION --> COLLECT_DETAILS: Discrepancy Resolved

    COLLECT_DETAILS --> GROUNDED_FAQ: Policy Question Asked
    GROUNDED_FAQ --> COLLECT_DETAILS: Cite Verified KB Excerpt

    COLLECT_DETAILS --> QUALIFICATION: All Required Entities Present
    QUALIFICATION --> RESULT: Underwrite (Approve Tier / Deny DTI)
    QUALIFICATION --> ESCALATION: Complex / Borderline Case

    COLLECT_DETAILS --> ESCALATION: Customer Requests Human Transfer
    RESULT --> [*]: Lead Dispatched to CRM
    ESCALATION --> [*]: Priority Transfer Dispatched to CRM
```

### Underwriting & Policy Grounding Rules:
* **Minimum Net Income**: $\$2,500$ / month.
* **Maximum DTI (Debt-to-Income)**: $45\%$.
* **Credit Score Tiers**:
  * **Tier 1 (750+)**: Fixed APR $6.49\%$.
  * **Tier 2 (680 - 749)**: Fixed APR $8.99\%$.
  * **Tier 3 (620 - 679)**: Fixed APR $12.49\%$.
  * **Tier 4 (< 620)**: Ineligible / Refer to Hardship Assistance.
* **Grounding Enforcement**: Any FAQ response MUST originate from Q2 retrieval chunks. If no relevant chunk matches confidence threshold, the agent responds with unsupported fallback: *"I do not have verified policy documentation on that topic. Let me connect you with a loan specialist."*

---

## 4. Q3 Multilingual Localization: Philippines & Indonesia

```mermaid
flowchart TD
    AudioIn["Incoming Utterance Stream"] --> Router["LanguageRouter"]
    Router --> Detect{"Dialect & Keyword Analysis"}

    Detect -->|"Tagalog / Taglish markers (po, opo, uutangin, kita)"| PH["Philippines Taglish Bot"]
    Detect -->|"Bahasa / Javanese markers (nggak, cicilan, tenor, nyuwun)"| ID["Indonesia Bahasa Bot"]
    Detect -->|"English markers or default"| US["Standard Voice Agent Engine"]

    subgraph PHBot["Philippines Domain Engine"]
        PH --> PH_Entities["PHP Currency & Suffix Normalizer (15k -> 15,000 PHP)"]
        PH_Entities --> PH_Terms["Insurance Lexicon: premium, beneficiary, rider, lapse, coverage"]
        PH_Terms --> PH_Register["Taglish Conversational Register ('Opo, i-check po natin')"]
    end

    subgraph IDBot["Indonesia Domain Engine"]
        ID --> ID_Entities["IDR Currency & Juta Multiplier (10jt -> 10,000,000 IDR)"]
        ID_Entities --> ID_Terms["Credit Lexicon: cicilan, tenor, denda, DP, angsuran"]
        ID_Terms --> ID_Register["Bahasa / Javanese Accent ('Nyuwun sewu, kulo cek rumiyin')"]
    end
```

---

## 5. Q4 Sub-Second Streaming & Real-Time Nudge Pipeline

```mermaid
flowchart TD
    AudioFrames["Live Audio Stream (250ms PCM Chunks)"] --> AudioBuf["AudioBuffer (Sliding Retention 60s)"]
    AudioFrames --> StreamASR["Streaming ASR (Simulated / Deepgram Nova-2)"]

    StreamASR --> TranscriptBuf["RollingTranscriptBuffer (Chronological Window)"]
    TranscriptBuf --> SigDetect["SignalDetector (Sub-millisecond Precompiled Automata)"]

    subgraph SignalRules["Signal Categories"]
        SigDetect --> S1["missed_cross_sell (Second car, family vehicle, protection rider)"]
        SigDetect --> S2["compliance_gap (Unauthorized guarantee, missing APR, missing consent)"]
        SigDetect --> S3["rising_frustration (Repetition complaints, transfer demands, negative sentiment)"]
        SigDetect --> S4["payment_difficulty (Job loss, medical crisis, delinquency/deferral request)"]
    end

    S1 --> NudgeEng["NudgeEngine"]
    S2 --> NudgeEng
    S3 --> NudgeEng
    S4 --> NudgeEng

    subgraph SuppressionEngine["Intelligent Filtering & Cooldown Policies"]
        NudgeEng --> C1{"Confidence >= 0.70?"}
        C1 -->|No| SuppressConf["Suppress: CONFIDENCE_TOO_LOW"]
        C1 -->|Yes| C2{"Cooldown Active (< 20s)?"}
        C2 -->|Yes| SuppressCD["Suppress: COOLDOWN_ACTIVE"]
        C2 -->|No| C3{"Repeat Limit Reached?"}
        C3 -->|Yes| SuppressRepeat["Suppress: MAX_REPEATS_REACHED"]
        C3 -->|No| EmitNudge["Emit Active Nudge (CRITICAL / HIGH / MEDIUM)"]
    end

    EmitNudge --> WSDispatcher["WebSocket ConnectionManager"]
    SuppressCD -.-> WSDispatcher
    WSDispatcher --> SupervisorUI["Live Supervisor Cockpit (apps/dashboard)"]
```

---

## 6. End-to-End Latency Profile

Measured across 100 sequential chunks in `q4_realtime/evaluation/benchmark.py`:

| Pipeline Stage | P50 (ms) | P95 (ms) | Allocation Target | Margin |
| :--- | :---: | :---: | :---: | :---: |
| 1. Audio Ingest & Sliding Buffer | `0.01` | `0.02` | 10 ms | 99.8% |
| 2. Streaming ASR Decoding | `35.08` | `35.21` | 400 ms | 91.2% |
| 3. Real-Time Signal Detection | `0.21` | `0.78` | 150 ms | 99.4% |
| 4. Nudge & Suppression Engine | `0.11` | `0.24` | 50 ms | 99.5% |
| **Total End-to-End Latency** | **`35.41`** | **`36.45`** | **1,000 ms** | **96.3%** |

---

## 7. Technology Stack & Key Dependencies

* **Language & Runtime**: Python 3.9+, Node.js (for asset tooling if needed).
* **API Framework**: FastAPI, Starlette, Uvicorn, WebSockets.
* **Vector & Natural Language Processing**: Scikit-Learn (TF-IDF vectorizer), NumPy, Regex.
* **Document Parsers**: PyPDF (`pypdf`), BeautifulSoup4 (`bs4`), Python-Docx (`docx`), Python standard `csv`.
* **Testing & Quality Assurance**: PyTest, PyTest-Asyncio.
* **Frontend Cockpit**: HTML5, Vanilla JavaScript, CSS3 Glassmorphism (no bulky node dependency locks for dashboard).
