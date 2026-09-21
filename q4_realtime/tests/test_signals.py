"""Unit tests for Q4 real-time signal detection."""

import pytest
from q4_realtime.schemas import SignalType, SpeakerRole, TranscriptChunk
from q4_realtime.signals.detector import SignalDetector


@pytest.mark.asyncio
async def test_missed_cross_sell_detection():
    detector = SignalDetector()
    call_id = "call-cross-sell"

    chunk = TranscriptChunk(
        chunk_id="c1",
        call_id=call_id,
        speaker=SpeakerRole.CUSTOMER,
        text="I also have a second car for my wife that might need coverage.",
    )
    signals = await detector.analyze_chunk(chunk)
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.MISSED_CROSS_SELL
    assert signals[0].confidence >= 0.90
    assert "second car" in signals[0].trigger_text


@pytest.mark.asyncio
async def test_compliance_gap_unauthorized_guarantee():
    detector = SignalDetector()
    call_id = "call-compliance-1"

    chunk = TranscriptChunk(
        chunk_id="c1",
        call_id=call_id,
        speaker=SpeakerRole.AGENT,
        text="Don't worry, you have guaranteed approval and no credit check is needed.",
    )
    signals = await detector.analyze_chunk(chunk)
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.COMPLIANCE_GAP
    assert signals[0].metadata["violation_type"] == "unauthorized_guarantee"


@pytest.mark.asyncio
async def test_compliance_gap_missing_apr():
    detector = SignalDetector()
    call_id = "call-compliance-2"

    chunk = TranscriptChunk(
        chunk_id="c1",
        call_id=call_id,
        speaker=SpeakerRole.AGENT,
        text="We can offer you a rate of 6.5% with a monthly payment of $350.",
    )
    # APR has NOT been disclosed yet
    signals = await detector.analyze_chunk(chunk)
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.COMPLIANCE_GAP
    assert signals[0].metadata["violation_type"] == "missing_apr_disclosure"


@pytest.mark.asyncio
async def test_rising_frustration_severe():
    detector = SignalDetector()
    call_id = "call-frust-1"

    chunk = TranscriptChunk(
        chunk_id="c1",
        call_id=call_id,
        speaker=SpeakerRole.CUSTOMER,
        text="I asked you three times already, this is ridiculous, speak to a human!",
    )
    signals = await detector.analyze_chunk(chunk)
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.RISING_FRUSTRATION
    assert signals[0].metadata["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_payment_difficulty_job_loss_and_medical():
    detector = SignalDetector()
    call_id = "call-pay-1"

    chunk1 = TranscriptChunk(
        chunk_id="c1",
        call_id=call_id,
        speaker=SpeakerRole.CUSTOMER,
        text="I recently got laid off from my job and cannot pay this month.",
    )
    signals1 = await detector.analyze_chunk(chunk1)
    assert len(signals1) >= 1
    assert any(s.signal_type == SignalType.PAYMENT_DIFFICULTY for s in signals1)

    chunk2 = TranscriptChunk(
        chunk_id="c2",
        call_id=call_id,
        speaker=SpeakerRole.CUSTOMER,
        text="We had unexpected hospital bills from an emergency surgery.",
    )
    signals2 = await detector.analyze_chunk(chunk2)
    assert len(signals2) == 1
    assert signals2[0].signal_type == SignalType.PAYMENT_DIFFICULTY
    assert signals2[0].metadata["hardship_category"] == "medical_crisis"

    # Verify detector latency stats
    stats = detector.get_latency_stats()
    assert stats["count"] >= 2
    assert stats["mean_ms"] < 10.0  # sub-millisecond to few ms
