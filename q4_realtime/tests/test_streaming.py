"""Unit tests for Q4 audio streaming buffer and rolling transcript buffer."""

import pytest
from q4_realtime.schemas import AudioChunk, AudioFormat, SpeakerRole, TranscriptChunk
from q4_realtime.streaming.buffer import AudioBuffer, RollingTranscriptBuffer
from q4_realtime.websocket.server import ConnectionManager


def test_audio_buffer_sliding_window():
    buffer = AudioBuffer(max_retention_ms=5000)
    call_id = "call-101"

    # Add 10 chunks spaced by 250ms
    base_ts = 1000000
    for i in range(10):
        chunk = AudioChunk(
            chunk_id=f"chk-{i}",
            call_id=call_id,
            speaker=SpeakerRole.CUSTOMER if i % 2 == 0 else SpeakerRole.AGENT,
            timestamp_ms=base_ts + (i * 250),
            duration_ms=250,
            audio_bytes=b"\x00\x01" * 125,
            is_speech=True,
        )
        buffer.add_chunk(chunk)

    stats = buffer.get_stats(call_id)
    assert stats["total_chunks"] == 10
    assert stats["total_duration_ms"] == 2500
    assert stats["speech_chunks"] == 10

    # Test window query: last 1000ms
    recent = buffer.get_window(call_id, window_ms=1000)
    assert len(recent) == 5  # chunks at 1250, 1500, 1750, 2000, 2250

    # Test speaker filter
    customer_chunks = buffer.get_window(call_id, window_ms=1000, speaker=SpeakerRole.CUSTOMER)
    assert all(c.speaker == SpeakerRole.CUSTOMER for c in customer_chunks)

    # Test byte concatenation
    combined = buffer.get_combined_bytes(call_id, window_ms=500)
    assert len(combined) > 0


def test_audio_buffer_eviction():
    # 1000ms retention
    buffer = AudioBuffer(max_retention_ms=1000)
    call_id = "call-102"

    chunk1 = AudioChunk(
        chunk_id="c1", call_id=call_id, timestamp_ms=1000, duration_ms=250, audio_bytes=b"a"
    )
    chunk2 = AudioChunk(
        chunk_id="c2", call_id=call_id, timestamp_ms=2500, duration_ms=250, audio_bytes=b"b"
    )

    buffer.add_chunk(chunk1)
    buffer.add_chunk(chunk2)

    # chunk1 at 1000 should have been evicted by cutoff (2500 - 1000 = 1500 > 1000)
    stats = buffer.get_stats(call_id)
    assert stats["total_chunks"] == 1

    buffer.clear_call(call_id)
    assert buffer.get_stats(call_id)["total_chunks"] == 0


def test_rolling_transcript_buffer():
    t_buffer = RollingTranscriptBuffer(max_turns=5, max_retention_ms=60000)
    call_id = "call-201"

    t_buffer.add_transcript(
        TranscriptChunk(
            chunk_id="t1",
            call_id=call_id,
            speaker=SpeakerRole.AGENT,
            text="Hello, thank you for calling Auto Credit.",
            timestamp_ms=1000,
        )
    )
    t_buffer.add_transcript(
        TranscriptChunk(
            chunk_id="t2",
            call_id=call_id,
            speaker=SpeakerRole.CUSTOMER,
            text="Hi, I want to ask about my loan balance.",
            timestamp_ms=2000,
        )
    )

    recent = t_buffer.get_recent_utterances(call_id, count=2)
    assert len(recent) == 2
    assert recent[0].speaker == SpeakerRole.AGENT

    text_window = t_buffer.get_window_text(call_id, window_ms=5000)
    assert "[AGENT]: Hello, thank you" in text_window
    assert "[CUSTOMER]: Hi, I want" in text_window

    ratio = t_buffer.compute_talk_ratio(call_id)
    assert 0.4 <= ratio <= 0.7  # Customer words vs Agent words


@pytest.mark.asyncio
async def test_websocket_connection_manager():
    manager = ConnectionManager()

    # Mock WebSocket
    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []
            self.accepted = False

        async def accept(self):
            self.accepted = True

        async def send_text(self, text: str):
            self.sent_messages.append(text)

    ws_call = MockWebSocket()
    ws_global = MockWebSocket()

    await manager.connect(ws_call, call_id="call-abc")
    await manager.connect(ws_global, call_id="global")

    assert ws_call.accepted
    assert ws_global.accepted

    # Broadcast to call-abc
    await manager.broadcast_to_call("call-abc", {"event": "test_signal", "val": 123})

    assert len(ws_call.sent_messages) == 1
    assert "test_signal" in ws_call.sent_messages[0]
    # Global listener also receives it
    assert len(ws_global.sent_messages) == 1

    # Disconnect
    manager.disconnect(ws_call, "call-abc")
    manager.disconnect(ws_global, None)
    assert "call-abc" not in manager.active_call_connections
    assert len(manager.global_connections) == 0
