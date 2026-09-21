"""
Voice provider factory.
"""
import os
from q1_voice_agent.providers.base import BaseVoiceProvider
from q1_voice_agent.providers.mock import MockVoiceProvider
from q1_voice_agent.providers.deepgram import DeepgramVoiceProvider

def get_voice_provider(provider_type: str = None) -> BaseVoiceProvider:
    choice = provider_type or os.getenv("VOICE_PROVIDER", "mock")
    if choice == "deepgram":
        return DeepgramVoiceProvider()
    return MockVoiceProvider()
