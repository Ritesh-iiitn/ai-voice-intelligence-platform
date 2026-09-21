"""Unit tests for streaming ASR decoders."""

import pytest
from q4_realtime.asr.streamer import MockStreamingASR, DeepgramStreamingASR
from q4_realtime.schemas import AudioChunk, SpeakerRole


@pytest.mark.asyncio
async def test_mock_streaming_asr():
    asr = MockStreamingASR(simulated_latency_ms=10.0)
    call_id = "test-call-asr"

    script = [
        (SpeakerRole.AGENT, "Hello, welcome to Lending Voice."),
        (SpeakerRole.CUSTOMER, "Hi, I am looking for a personal loan."),
        (SpeakerRole.AGENT, "Certainly! May I get your monthly income?"),
    ]
    asr.queue_script(call_id, script)

    # Ingest 3 chunks
    res1 = await asr.feed_chunk(
        AudioChunk(chunk_id="c1", call_id=call_id, audio_bytes=b"\x00" * 500)
    )
    assert res1 is not None
    assert res1.speaker == SpeakerRole.AGENT
    assert "welcome to Lending Voice" in res1.text

    res2 = await asr.feed_chunk(
        AudioChunk(chunk_id="c2", call_id=call_id, audio_bytes=b"\x00" * 500)
    )
    assert res2 is not None
    assert res2.speaker == SpeakerRole.CUSTOMER
    assert "personal loan" in res2.text

    # Latency stats should be tracked
    stats = asr.get_latency_stats(call_id)
    assert stats["samples"] == 2
    assert stats["mean_ms"] >= 8.0  # Simulated latency >= 10ms approx

    # Flush remaining
    res3 = await asr.flush(call_id)
    assert res3 is not None
    assert "monthly income" in res3.text

    # Further flush returns None
    res4 = await asr.flush(call_id)
    assert res4 is None


@pytest.mark.asyncio
async def test_deepgram_fallback_without_keys():
    # Tests that when mock or invalid key is given, it gracefully handles without crashing
    asr = DeepgramStreamingASR(api_key="mock_key_test")
    call_id = "dg-fallback-call"

    chunk = AudioChunk(chunk_id="c-dg-1", call_id=call_id, audio_bytes=b"\x00" * 100)
    result = await asr.feed_chunk(chunk)
    assert result is None  # Mock key returns None without error

    stats = asr.get_latency_stats(call_id)
    assert stats["samples"] == 1
