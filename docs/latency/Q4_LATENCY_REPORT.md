# Q4 Real-Time Pipeline Latency Benchmark Report

## Executive Summary
This report evaluates the empirical end-to-end latency of the sub-second streaming audio, transcription, signal detection, and nudge generation pipeline across 100 sequential stream frames.

* **Target Sub-Second SLA**: `< 1000 ms`
* **Observed E2E P95 Latency**: `36.54 ms`
* **SLA Status**: ✅ PASS (Sub-second SLA met with >90% margin)

---

## Component Latency Breakdown (100 Samples)

| Pipeline Stage | Mean Latency (ms) | P50 / Median (ms) | P95 Latency (ms) | P99 Latency (ms) | Budget Allocation | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Audio Ingest & Sliding Buffer** | `0.03` | `0.03` | `0.04` | `0.05` | 10 ms | ✅ Optimal |
| **2. Streaming ASR Decoding** | `36.2` | `36.26` | `36.33` | `36.38` | 400 ms | ✅ Optimal |
| **3. Real-Time Signal Detection** | `0.08` | `0.08` | `0.12` | `0.13` | 150 ms | ✅ Optimal |
| **4. Nudge & Suppression Engine** | `0.04` | `0.04` | `0.09` | `0.1` | 50 ms | ✅ Optimal |
| **Total End-to-End Pipeline** | **`36.37`** | **`36.42`** | **`36.54`** | **`36.62`** | **1,000 ms** | **✅ PASS (Sub-second SLA met with >90% margin)** |

---

## Architectural Latency Optimizations
1. **Zero-Copy In-Memory Audio Ring Buffer**:
   - Chunks (250ms PCM) are appended with $O(1)$ time complexity into a bounded double-ended queue.
   - Buffer eviction is strictly chronological, preventing memory ballooning during prolonged calls.
2. **Deterministic Pre-compiled Regular Expressions**:
   - Signal matching utilizes pre-compiled regex automata with boundary checks, executing in `< 1.5ms` per turn.
   - Avoids costly LLM round-trips for real-time compliance and risk signals.
3. **Local State Machine Cooldowns**:
   - Nudge suppression evaluates a 20-second rolling window and repeat limits in `< 0.2ms` per detected signal.
4. **WebSocket Non-Blocking Asyncio Broadcast**:
   - Dispatches telemetry payloads directly over non-blocking websockets to active agent browser sessions.

---
*Report generated automatically by `q4_realtime/evaluation/benchmark.py`.*
