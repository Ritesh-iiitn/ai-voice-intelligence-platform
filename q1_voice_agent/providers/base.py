"""
Abstract base interface for voice telephony, ASR, and TTS providers.
"""
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator

class BaseVoiceProvider(ABC):
    """Abstract interface decoupling voice provider implementations from core agent logic."""

    @abstractmethod
    def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Synthesize text into audio bytes."""
        pass

    @abstractmethod
    def transcribe_audio_chunk(self, chunk: bytes) -> str:
        """Transcribe an incoming streaming audio chunk."""
        pass
