"""
Mock Voice Provider for standalone local testing and development.
Generates synthetic WAV audio headers and simulated transcriptions.
"""
import struct
from typing import Optional
from q1_voice_agent.providers.base import BaseVoiceProvider

class MockVoiceProvider(BaseVoiceProvider):
    """Local offline provider generating minimal valid PCM/WAV byte streams."""

    def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Generates a minimal valid 16kHz mono WAV file header with silence."""
        sample_rate = 16000
        num_samples = min(sample_rate * 2, max(len(text) * 400, 8000))
        data_size = num_samples * 2  # 16-bit
        
        # Build RIFF WAV header
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,
            1,  # PCM
            1,  # Mono
            sample_rate,
            sample_rate * 2,
            2,  # Block align
            16, # Bits per sample
            b"data",
            data_size
        )
        # Append silence or mock pulse
        body = b"\x00" * data_size
        return header + body

    def transcribe_audio_chunk(self, chunk: bytes) -> str:
        """Simulate decoding an incoming audio chunk."""
        if not chunk or len(chunk) < 44:
            return ""
        return "Simulated customer speech decoded from PCM audio chunk."
