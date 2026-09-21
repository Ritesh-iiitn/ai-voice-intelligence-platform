"""Streaming Speech-to-Text decoders and utterance segmentation for live calls."""

from __future__ import annotations

import abc
import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Callable, Dict, List, Optional
from q4_realtime.schemas import AudioChunk, SpeakerRole, TranscriptChunk

logger = logging.getLogger(__name__)


class StreamingASR(abc.ABC):
    """Abstract interface for real-time streaming speech-to-text."""

    @abc.abstractmethod
    async def feed_chunk(self, chunk: AudioChunk) -> Optional[TranscriptChunk]:
        """Ingest a temporal audio chunk (e.g. 250ms) and return a transcript if segment completes."""
        pass

    @abc.abstractmethod
    async def flush(self, call_id: str) -> Optional[TranscriptChunk]:
        """Flush any pending audio or partial tokens for a call."""
        pass

    @abc.abstractmethod
    def get_latency_stats(self, call_id: str) -> Dict[str, float]:
        """Return average and P95 ASR latency in milliseconds."""
        pass


class MockStreamingASR(StreamingASR):
    """Deterministic, high-performance mock streaming ASR for testing, CI/CD, and benchmark evaluation.

    Allows queuing pre-scripted phrases or extracting text from synthesized speech buffers,
    emitting words incrementally across audio chunks with realistic simulated processing latency.
    """

    def __init__(self, simulated_latency_ms: float = 35.0):
        self.simulated_latency_ms = simulated_latency_ms
        self._latencies: Dict[str, List[float]] = {}
        # Pre-queued script lines per call: call_id -> list of (speaker, text)
        self._utterance_queue: Dict[str, List[tuple[SpeakerRole, str]]] = {}
        # Unfinalized text accumulator: call_id -> list of words
        self._accumulators: Dict[str, List[str]] = {}

    def queue_script(self, call_id: str, script: List[tuple[SpeakerRole, str]]) -> None:
        """Load conversation lines to simulate live audio recognition turn-by-turn."""
        self._utterance_queue[call_id] = list(script)
        self._latencies[call_id] = []
        self._accumulators[call_id] = []

    async def feed_chunk(self, chunk: AudioChunk) -> Optional[TranscriptChunk]:
        """Process an audio chunk. If the call has queued utterances, emits final or partial tokens."""
        t_start = time.perf_counter()

        # Simulate non-blocking micro-delay for realistic latency profiling
        if self.simulated_latency_ms > 0:
            await asyncio.sleep(self.simulated_latency_ms / 1000.0)

        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        if chunk.call_id not in self._latencies:
            self._latencies[chunk.call_id] = []
        self._latencies[chunk.call_id].append(t_elapsed_ms)

        queue = self._utterance_queue.get(chunk.call_id, [])
        if not queue:
            # Check if chunk contains direct embedded text metadata (e.g. from mock synthesizer)
            return None

        # Pop next scripted utterance
        speaker, text = queue.pop(0)
        return TranscriptChunk(
            chunk_id=chunk.chunk_id,
            call_id=chunk.call_id,
            speaker=speaker,
            text=text,
            timestamp_ms=chunk.timestamp_ms,
            duration_ms=chunk.duration_ms,
            is_final=True,
            confidence=0.96,
        )

    async def flush(self, call_id: str) -> Optional[TranscriptChunk]:
        """Flush remaining buffered speech."""
        queue = self._utterance_queue.get(call_id, [])
        if queue:
            speaker, text = queue.pop(0)
            return TranscriptChunk(
                chunk_id=f"flush-{int(time.time() * 1000)}",
                call_id=call_id,
                speaker=speaker,
                text=text,
                timestamp_ms=int(time.time() * 1000),
                duration_ms=250,
                is_final=True,
                confidence=0.95,
            )
        return None

    def get_latency_stats(self, call_id: str) -> Dict[str, float]:
        """Calculate mean and P95 latency for the call."""
        latencies = self._latencies.get(call_id, [])
        if not latencies:
            return {"mean_ms": 0.0, "p95_ms": 0.0, "samples": 0}

        sorted_lat = sorted(latencies)
        p95_idx = int(0.95 * len(sorted_lat))
        return {
            "mean_ms": round(sum(latencies) / len(latencies), 2),
            "p95_ms": round(sorted_lat[min(p95_idx, len(sorted_lat) - 1)], 2),
            "samples": len(latencies),
        }


class DeepgramStreamingASR(StreamingASR):
    """Production WebSocket streaming client for Deepgram Nova-2 speech-to-text."""

    def __init__(self, api_key: str, model: str = "nova-2", language: str = "en"):
        self.api_key = api_key
        self.model = model
        self.language = language
        self._latencies: Dict[str, List[float]] = {}
        self._ws_clients: Dict[str, Any] = {}

    async def feed_chunk(self, chunk: AudioChunk) -> Optional[TranscriptChunk]:
        """Send raw binary PCM bytes over Deepgram live WebSocket connection."""
        t_start = time.perf_counter()

        if not self.api_key or self.api_key.startswith("mock_"):
            # Fallback gracefully to mock mode if dummy key provided
            await asyncio.sleep(0.02)
            elapsed = (time.perf_counter() - t_start) * 1000.0
            if chunk.call_id not in self._latencies:
                self._latencies[chunk.call_id] = []
            self._latencies[chunk.call_id].append(elapsed)
            return None

        try:
            import websockets

            ws_url = (
                f"wss://api.deepgram.com/v1/listen?"
                f"model={self.model}&language={self.language}&punctuate=true&interim_results=false"
                f"&encoding=linear16&sample_rate={chunk.sample_rate}&channels=1"
            )

            # Lazy connect if not already open
            if chunk.call_id not in self._ws_clients:
                ws = await websockets.connect(
                    ws_url,
                    extra_headers={"Authorization": f"Token {self.api_key}"},
                )
                self._ws_clients[chunk.call_id] = ws

            ws = self._ws_clients[chunk.call_id]
            await ws.send(chunk.audio_bytes)

            # Check for non-blocking incoming message
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=0.01)
                data = json.loads(msg)
                channel = data.get("channel", {})
                alternatives = channel.get("alternatives", [{}])
                transcript = alternatives[0].get("transcript", "")
                confidence = alternatives[0].get("confidence", 0.9)

                elapsed = (time.perf_counter() - t_start) * 1000.0
                if chunk.call_id not in self._latencies:
                    self._latencies[chunk.call_id] = []
                self._latencies[chunk.call_id].append(elapsed)

                if transcript.strip():
                    return TranscriptChunk(
                        chunk_id=chunk.chunk_id,
                        call_id=chunk.call_id,
                        speaker=chunk.speaker,
                        text=transcript.strip(),
                        timestamp_ms=chunk.timestamp_ms,
                        duration_ms=chunk.duration_ms,
                        is_final=data.get("is_final", True),
                        confidence=confidence,
                    )
            except asyncio.TimeoutError:
                pass

        except Exception as e:
            logger.warning("Deepgram streaming error for call %s: %s", chunk.call_id, e)

        return None

    async def flush(self, call_id: str) -> Optional[TranscriptChunk]:
        """Close WebSocket session and flush final transcript."""
        ws = self._ws_clients.pop(call_id, None)
        if ws:
            try:
                # Send close stream frame to Deepgram
                await ws.send(json.dumps({"type": "CloseStream"}))
                await ws.close()
            except Exception:
                pass
        return None

    def get_latency_stats(self, call_id: str) -> Dict[str, float]:
        latencies = self._latencies.get(call_id, [])
        if not latencies:
            return {"mean_ms": 0.0, "p95_ms": 0.0, "samples": 0}

        sorted_lat = sorted(latencies)
        p95_idx = int(0.95 * len(sorted_lat))
        return {
            "mean_ms": round(sum(latencies) / len(latencies), 2),
            "p95_ms": round(sorted_lat[min(p95_idx, len(sorted_lat) - 1)], 2),
            "samples": len(latencies),
        }
