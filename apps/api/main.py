"""FastAPI Application uniting Knowledge Base, Voice Agent, Multilingual Localization, and Live Q4 Telemetry."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from q2_knowledge_base.retrieval.hybrid import HybridRetriever
from q2_knowledge_base.retrieval.citation import CitationFormatter
from q1_voice_agent.agent.engine import VoiceAgentEngine
from q1_voice_agent.agent.state_machine import ConversationState
from q3_multilingual.localization.language_router import LanguageRouter, SupportedMarket
from q4_realtime.schemas import (
    AudioChunk,
    NudgePayload,
    SignalPayload,
    SpeakerRole,
    TranscriptChunk,
    WebSocketMessage,
)
from q4_realtime.streaming.buffer import AudioBuffer, RollingTranscriptBuffer
from q4_realtime.asr.streamer import MockStreamingASR
from q4_realtime.signals.detector import SignalDetector, get_signal_detector
from q4_realtime.nudges.engine import NudgeEngine, get_nudge_engine
from q4_realtime.websocket.server import ConnectionManager, get_connection_manager

logger = logging.getLogger("apps.api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Production Voice AI & Real-Time Nudge Platform",
    version="1.0.0",
    description="Unified API for Q1 Grounded Voice Agent, Q2 Knowledge Base, Q3 Multilingual Localization, and Q4 Real-Time Nudges",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
connection_manager = get_connection_manager()
signal_detector = get_signal_detector()
nudge_engine = get_nudge_engine()
audio_buffer = AudioBuffer()
transcript_buffer = RollingTranscriptBuffer()
language_router = LanguageRouter()

# Knowledge Base & Agent singletons
_kb_retriever: Optional[HybridRetriever] = None
_call_states: Dict[str, ConversationState] = {}
_voice_agents: Dict[str, VoiceAgentEngine] = {}


def get_kb_retriever() -> HybridRetriever:
    global _kb_retriever
    if _kb_retriever is None:
        from q2_knowledge_base.ingestion.reader import DocumentIngestor
        from q2_knowledge_base.cleaning.cleaner import DocumentCleaner
        from q2_knowledge_base.chunking.chunker import SemanticSectionChunker
        from q2_knowledge_base.embeddings.local import LocalVectorEmbeddingProvider
        from q2_knowledge_base.indexing.vector_index import VectorIndex
        from q2_knowledge_base.retrieval.bm25 import BM25Retriever

        docs = DocumentIngestor().ingest_directory("data/source_documents")
        cleaner = DocumentCleaner()
        chunker = SemanticSectionChunker()

        chunks = []
        for d in docs:
            if d.status == "success":
                d.content = cleaner.clean_text(d.content)
                chunks.extend(chunker.chunk_document(d))

        v_idx = VectorIndex(embedding_provider=LocalVectorEmbeddingProvider())
        v_idx.build_index(chunks)

        bm25_idx = BM25Retriever()
        bm25_idx.build_index(chunks)

        _kb_retriever = HybridRetriever(vector_index=v_idx, bm25_retriever=bm25_idx)
    return _kb_retriever


# Request / Response models
class KBSearchRequest(BaseModel):
    query: str
    top_k: int = 3
    filter_metadata: Optional[Dict[str, Any]] = None


class VoiceTurnRequest(BaseModel):
    call_id: str
    customer_speech: str


class SimulateStreamTurnRequest(BaseModel):
    call_id: str
    speaker: SpeakerRole
    text: str
    timestamp_ms: Optional[int] = None


class MultilingualRouteRequest(BaseModel):
    text: str
    detected_country_code: Optional[str] = None


class ResetCallRequest(BaseModel):
    call_id: str = "call-live-101"


# ---------------- API ENDPOINTS ---------------- #

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Voice AI Platform",
        "modules": ["q1_voice_agent", "q2_knowledge_base", "q3_multilingual", "q4_realtime"],
        "timestamp_ms": int(time.time() * 1000),
    }


@app.post("/api/calls/reset")
async def reset_call(req: ResetCallRequest):
    """Resets conversational state and nudges for a given call session."""
    retriever = get_kb_retriever()
    _voice_agents[req.call_id] = VoiceAgentEngine(retriever=retriever)
    _call_states[req.call_id] = ConversationState(call_id=req.call_id)
    if req.call_id in nudge_engine._states:
        del nudge_engine._states[req.call_id]
    return {"status": "reset", "call_id": req.call_id}


@app.post("/api/kb/search")
async def search_kb(req: KBSearchRequest):
    """Retrieve grounded knowledge base passages with BM25 and vector fusion."""
    retriever = get_kb_retriever()
    results = retriever.retrieve(req.query, top_k=req.top_k, filters=req.filter_metadata)
    citations = [CitationFormatter.format_citation(res) for res in results]
    return {
        "query": req.query,
        "results_count": len(results),
        "results": [
            {
                "chunk_id": r.chunk_id,
                "source": r.source,
                "section": r.section,
                "score": round(r.score, 4),
                "content": r.content,
            }
            for r in results
        ],
        "citations": citations,
    }


@app.post("/api/voice/process-turn")
async def process_voice_turn(req: VoiceTurnRequest):
    """Execute a single conversational turn in the grounded Q1 voice state machine."""
    retriever = get_kb_retriever()
    if req.call_id not in _voice_agents:
        _voice_agents[req.call_id] = VoiceAgentEngine(retriever=retriever)
        _call_states[req.call_id] = ConversationState(call_id=req.call_id)

    agent = _voice_agents[req.call_id]
    state = _call_states[req.call_id]
    result = agent.process_turn(state, req.customer_speech)
    return {
        "call_id": req.call_id,
        "agent_response": result.get("response", ""),
        "current_state": result.get("state", state.current_state.value),
        "escalated": result.get("escalation_requested", False),
        "citations": result.get("citations", []),
        "qualification_completed": result.get("qualification_status") is not None,
    }


@app.post("/api/multilingual/route")
async def route_multilingual(req: MultilingualRouteRequest):
    """Detect language, dialect, and route to Philippines Taglish or Indonesia Bahasa bot."""
    decision = language_router.route(req.text, country_code=req.detected_country_code)
    return {
        "text": req.text,
        "market": decision.market.value,
        "confidence": decision.confidence,
        "detected_markers": decision.detected_markers,
        "selected_bot": decision.bot_engine_name,
    }


@app.post("/api/calls/simulate-turn")
async def simulate_stream_turn(req: SimulateStreamTurnRequest):
    """Simulate an incoming streaming utterance, run detection & nudge engines, and push via WebSocket."""
    t0 = time.perf_counter()
    ts = req.timestamp_ms or int(time.time() * 1000)

    # 1. Ingest transcript into buffer
    transcript_chunk = TranscriptChunk(
        chunk_id=f"chk-{int(time.time()*1000)}",
        call_id=req.call_id,
        speaker=req.speaker,
        text=req.text,
        timestamp_ms=ts,
        duration_ms=len(req.text.split()) * 300,
        is_final=True,
        confidence=0.95,
    )
    transcript_buffer.add_transcript(transcript_chunk)

    # Broadcast transcript chunk to WebSocket listeners
    await connection_manager.broadcast_to_call(
        req.call_id,
        WebSocketMessage(
            event_type="transcript",
            payload=transcript_chunk.model_dump(),
        ),
    )

    # 2. Run signal detection
    t_sig_start = time.perf_counter()
    signals = await signal_detector.analyze_chunk(transcript_chunk)
    sig_latency_ms = (time.perf_counter() - t_sig_start) * 1000.0

    nudges: List[NudgePayload] = []
    # 3. For each signal, run NudgeEngine
    for sig in signals:
        await connection_manager.broadcast_to_call(
            req.call_id,
            WebSocketMessage(
                event_type="signal",
                payload=sig.model_dump(),
            ),
        )

        nudge = nudge_engine.generate_nudge(sig)
        nudges.append(nudge)

        # Broadcast nudge (including suppression flag)
        await connection_manager.broadcast_to_call(
            req.call_id,
            WebSocketMessage(
                event_type="nudge",
                payload=nudge.model_dump(),
            ),
        )

    # 4. Compute updated call metrics
    talk_ratio = transcript_buffer.compute_talk_ratio(req.call_id)
    total_latency_ms = (time.perf_counter() - t0) * 1000.0

    metrics_payload = {
        "call_id": req.call_id,
        "customer_talk_ratio": talk_ratio,
        "signals_count": len(signals),
        "nudges_count": len(nudges),
        "total_latency_ms": round(total_latency_ms, 2),
        "sig_latency_ms": round(sig_latency_ms, 2),
    }

    await connection_manager.broadcast_to_call(
        req.call_id,
        WebSocketMessage(
            event_type="metrics",
            payload=metrics_payload,
        ),
    )

    return {
        "status": "processed",
        "call_id": req.call_id,
        "signals_detected": [s.model_dump() for s in signals],
        "nudges_generated": [n.model_dump() for n in nudges],
        "latency_ms": round(total_latency_ms, 2),
    }


# ---------------- WEBSOCKET STREAM ---------------- #

@app.websocket("/ws/calls/{call_id}")
async def websocket_call_stream(websocket: WebSocket, call_id: str):
    """Bidirectional WebSocket for live call audio/text stream and instant nudge delivery."""
    await connection_manager.connect(websocket, call_id)
    logger.info("WebSocket connected for call %s", call_id)
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("event_type")

            if event_type == "ping":
                await websocket.send_json({"event_type": "pong", "timestamp_ms": int(time.time() * 1000)})
            elif event_type == "transcript_input":
                # Process streamed transcript
                req = SimulateStreamTurnRequest(
                    call_id=call_id,
                    speaker=SpeakerRole(data.get("speaker", "CUSTOMER")),
                    text=data.get("text", ""),
                )
                await simulate_stream_turn(req)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, call_id)
        logger.info("WebSocket disconnected for call %s", call_id)
    except Exception as e:
        logger.error("WebSocket exception: %s", e)
        connection_manager.disconnect(websocket, call_id)


# Mount static files for dashboard
dashboard_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard"))
if os.path.exists(dashboard_dir):
    app.mount("/static", StaticFiles(directory=dashboard_dir), name="static")


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the real-time agent dashboard UI."""
    index_file = os.path.join(dashboard_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h3>Dashboard file index.html is being prepared...</h3>")
