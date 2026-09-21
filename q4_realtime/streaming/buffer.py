"""Thread-safe sliding window audio and transcript buffers for real-time speech processing."""

from __future__ import annotations

import collections
import threading
from typing import Dict, List, Optional
from q4_realtime.schemas import AudioChunk, SpeakerRole, TranscriptChunk


class AudioBuffer:
    """Sliding-window buffer managing temporal audio chunks (e.g. 250ms chunks) per call.

    Maintains a bounded time-window of raw PCM audio to prevent memory leaks while
    providing instantaneous slices for streaming ASR decoders or VAD models.
    """

    def __init__(self, max_retention_ms: int = 60000):
        self.max_retention_ms = max_retention_ms
        self._buffers: Dict[str, List[AudioChunk]] = collections.defaultdict(list)
        self._lock = threading.RLock()

    def add_chunk(self, chunk: AudioChunk) -> None:
        """Append an audio chunk and prune items exceeding max retention."""
        with self._lock:
            call_chunks = self._buffers[chunk.call_id]
            call_chunks.append(chunk)

            # Evict old chunks outside retention window
            cutoff_ts = chunk.timestamp_ms - self.max_retention_ms
            while call_chunks and call_chunks[0].timestamp_ms < cutoff_ts:
                call_chunks.pop(0)

    def get_window(
        self,
        call_id: str,
        window_ms: int = 5000,
        speaker: Optional[SpeakerRole] = None,
    ) -> List[AudioChunk]:
        """Retrieve recent chunks within the last `window_ms` milliseconds."""
        with self._lock:
            chunks = self._buffers.get(call_id, [])
            if not chunks:
                return []

            latest_ts = chunks[-1].timestamp_ms
            cutoff_ts = latest_ts - window_ms

            filtered = [
                c for c in chunks
                if c.timestamp_ms >= cutoff_ts
                and (speaker is None or c.speaker == speaker)
            ]
            return list(filtered)

    def get_combined_bytes(
        self,
        call_id: str,
        window_ms: int = 5000,
        speaker: Optional[SpeakerRole] = None,
    ) -> bytes:
        """Concatenate raw PCM audio bytes across the requested sliding window."""
        chunks = self.get_window(call_id, window_ms=window_ms, speaker=speaker)
        return b"".join(c.audio_bytes for c in chunks)

    def get_stats(self, call_id: str) -> dict:
        """Compute buffer statistics including duration and chunk counts."""
        with self._lock:
            chunks = self._buffers.get(call_id, [])
            if not chunks:
                return {"total_chunks": 0, "total_duration_ms": 0, "speech_chunks": 0}

            total_dur = sum(c.duration_ms for c in chunks)
            speech_chunks = sum(1 for c in chunks if c.is_speech)
            return {
                "total_chunks": len(chunks),
                "total_duration_ms": total_dur,
                "speech_chunks": speech_chunks,
            }

    def clear_call(self, call_id: str) -> None:
        """Clear memory for a terminated call."""
        with self._lock:
            self._buffers.pop(call_id, None)


class RollingTranscriptBuffer:
    """Sliding-window buffer managing incremental and final transcript segments."""

    def __init__(self, max_turns: int = 50, max_retention_ms: int = 180000):
        self.max_turns = max_turns
        self.max_retention_ms = max_retention_ms
        self._transcripts: Dict[str, List[TranscriptChunk]] = collections.defaultdict(list)
        self._lock = threading.RLock()

    def add_transcript(self, chunk: TranscriptChunk) -> None:
        """Append a transcript chunk and maintain bounded window."""
        with self._lock:
            call_items = self._transcripts[chunk.call_id]
            call_items.append(chunk)

            # Evict if exceeding max turns or max retention
            cutoff_ts = chunk.timestamp_ms - self.max_retention_ms
            while len(call_items) > self.max_turns or (
                call_items and call_items[0].timestamp_ms < cutoff_ts
            ):
                call_items.pop(0)

    def get_recent_utterances(self, call_id: str, count: int = 5) -> List[TranscriptChunk]:
        """Retrieve the latest N transcript segments."""
        with self._lock:
            items = self._transcripts.get(call_id, [])
            return list(items[-count:])

    def get_window_text(
        self,
        call_id: str,
        window_ms: int = 30000,
        speaker: Optional[SpeakerRole] = None,
    ) -> str:
        """Get formatted dialogue text within the specified recent duration window."""
        with self._lock:
            items = self._transcripts.get(call_id, [])
            if not items:
                return ""

            latest_ts = items[-1].timestamp_ms
            cutoff_ts = latest_ts - window_ms

            filtered = [
                f"[{it.speaker.value}]: {it.text}"
                for it in items
                if it.timestamp_ms >= cutoff_ts
                and (speaker is None or it.speaker == speaker)
            ]
            return "\n".join(filtered)

    def get_full_transcript(self, call_id: str) -> List[TranscriptChunk]:
        """Return all available transcript chunks for a call."""
        with self._lock:
            return list(self._transcripts.get(call_id, []))

    def compute_talk_ratio(self, call_id: str) -> float:
        """Compute the ratio of Customer words to Total words (0.0 to 1.0)."""
        with self._lock:
            items = self._transcripts.get(call_id, [])
            if not items:
                return 0.5

            customer_words = 0
            agent_words = 0

            for it in items:
                words = len(it.text.split())
                if it.speaker == SpeakerRole.CUSTOMER:
                    customer_words += words
                elif it.speaker == SpeakerRole.AGENT:
                    agent_words += words

            total = customer_words + agent_words
            if total == 0:
                return 0.5
            return round(customer_words / total, 3)

    def clear_call(self, call_id: str) -> None:
        """Clear transcripts for a terminated call."""
        with self._lock:
            self._transcripts.pop(call_id, None)
