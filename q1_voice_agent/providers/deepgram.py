"""
Production Deepgram adapter with offline mock fallback.
"""
import os
import logging
from typing import Optional
from q1_voice_agent.providers.base import BaseVoiceProvider
from q1_voice_agent.providers.mock import MockVoiceProvider

logger = logging.getLogger(__name__)

class DeepgramVoiceProvider(BaseVoiceProvider):
    """Deepgram ASR and TTS adapter."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        self.fallback = MockVoiceProvider()
        if not self.api_key:
            logger.info("DEEPGRAM_API_KEY not configured. Operating in mock adapter fallback mode.")

    def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        if not self.api_key:
            return self.fallback.synthesize_speech(text, voice_id)
        # Production Deepgram REST TTS call
        try:
            import httpx
            url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
            headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}
            resp = httpx.post(url, headers=headers, json={"text": text}, timeout=10.0)
            if resp.status_code == 200:
                return resp.content
            logger.warning(f"Deepgram TTS API returned {resp.status_code}, falling back to mock.")
            return self.fallback.synthesize_speech(text, voice_id)
        except Exception as e:
            logger.error(f"Deepgram TTS failed: {e}")
            return self.fallback.synthesize_speech(text, voice_id)

    def transcribe_audio_chunk(self, chunk: bytes) -> str:
        if not self.api_key:
            return self.fallback.transcribe_audio_chunk(chunk)
        # Production Deepgram REST ASR call
        try:
            import httpx
            url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
            headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "audio/wav"}
            resp = httpx.post(url, headers=headers, content=chunk, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                channels = data.get("results", {}).get("channels", [])
                if channels and channels[0].get("alternatives"):
                    return channels[0]["alternatives"][0].get("transcript", "")
            return self.fallback.transcribe_audio_chunk(chunk)
        except Exception as e:
            logger.error(f"Deepgram ASR failed: {e}")
            return self.fallback.transcribe_audio_chunk(chunk)
