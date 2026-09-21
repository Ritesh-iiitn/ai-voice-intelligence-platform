"""Data models and schemas for Q4 Real-Time Streaming, Signal Detection, and Nudges."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
import time
from pydantic import BaseModel, Field


class SpeakerRole(str, Enum):
    """Speaker roles in a conversational voice stream."""
    AGENT = "AGENT"
    CUSTOMER = "CUSTOMER"
    SYSTEM = "SYSTEM"


class SignalType(str, Enum):
    """Real-time business signals detected from live speech."""
    MISSED_CROSS_SELL = "missed_cross_sell"
    COMPLIANCE_GAP = "compliance_gap"
    RISING_FRUSTRATION = "rising_frustration"
    PAYMENT_DIFFICULTY = "payment_difficulty"


class NudgePriority(str, Enum):
    """Priority level for supervisor/agent nudges."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AudioFormat(str, Enum):
    """Supported streaming audio encodings."""
    PCM_16BIT_16KHZ = "pcm_16bit_16khz"
    WAV = "wav"
    RAW_BASE64 = "raw_base64"


class AudioChunk(BaseModel):
    """A discrete temporal chunk of audio stream (e.g., 250ms)."""
    chunk_id: str
    call_id: str
    speaker: SpeakerRole = SpeakerRole.CUSTOMER
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    duration_ms: int = 250
    audio_bytes: bytes = Field(default=b"")
    sample_rate: int = 16000
    format: AudioFormat = AudioFormat.PCM_16BIT_16KHZ
    is_speech: bool = True
    model_config = {"arbitrary_types_allowed": True}


class TranscriptChunk(BaseModel):
    """A streaming transcription segment with timing and speaker tagging."""
    chunk_id: str
    call_id: str
    speaker: SpeakerRole
    text: str
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    duration_ms: int = 250
    is_final: bool = True
    confidence: float = 1.0


class SignalPayload(BaseModel):
    """A detected conversational signal with supporting evidence."""
    signal_id: str
    call_id: str
    signal_type: SignalType
    speaker: SpeakerRole
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    trigger_text: str
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NudgePayload(BaseModel):
    """An actionable prompt or compliance warning dispatched to the agent UI."""
    nudge_id: str
    call_id: str
    signal_type: SignalType
    priority: NudgePriority
    title: str
    message: str
    recommended_script: str
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    confidence: float = 1.0
    suppressed: bool = False
    suppression_reason: Optional[str] = None
    trigger_text: Optional[str] = None


class CallMetrics(BaseModel):
    """Live metrics updated incrementally during call lifecycle."""
    call_id: str
    duration_ms: int = 0
    total_chunks: int = 0
    total_words: int = 0
    customer_talk_ratio: float = 0.5
    signals_detected: int = 0
    nudges_emitted: int = 0
    average_latency_ms: float = 0.0


class WebSocketMessage(BaseModel):
    """Wire envelope for WebSocket events sent to browser or dashboard."""
    event_type: str  # 'audio_chunk', 'transcript', 'signal', 'nudge', 'metrics', 'ping', 'pong'
    payload: Dict[str, Any]
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
