"""Unit tests for NudgeEngine suppression, cooldowns, and priority ordering."""

import pytest
from q4_realtime.nudges.engine import NudgeEngine
from q4_realtime.schemas import NudgePriority, SignalPayload, SignalType, SpeakerRole


def test_nudge_generation_and_priorities():
    engine = NudgeEngine(cooldown_seconds=20.0, min_confidence_threshold=0.70)
    call_id = "test-call-nudge-1"

    # 1. Critical compliance signal
    sig1 = SignalPayload(
        signal_id="s1",
        call_id=call_id,
        signal_type=SignalType.COMPLIANCE_GAP,
        speaker=SpeakerRole.AGENT,
        timestamp_ms=1000,
        trigger_text="You are 100% approved guaranteed!",
        confidence=0.98,
        metadata={"violation_type": "unauthorized_guarantee"},
    )
    nudge1 = engine.generate_nudge(sig1)
    assert not nudge1.suppressed
    assert nudge1.priority == NudgePriority.CRITICAL
    assert "MANDATORY CORRECTION" in nudge1.title
    assert "pre-qualification" in nudge1.recommended_script

    # 2. Cross-sell signal
    sig2 = SignalPayload(
        signal_id="s2",
        call_id=call_id,
        signal_type=SignalType.MISSED_CROSS_SELL,
        speaker=SpeakerRole.CUSTOMER,
        timestamp_ms=2000,
        trigger_text="I have a second car for my husband.",
        confidence=0.92,
        metadata={"opportunity": "multi_vehicle_bundle"},
    )
    nudge2 = engine.generate_nudge(sig2)
    assert not nudge2.suppressed
    assert nudge2.priority == NudgePriority.MEDIUM
    assert "Multi-Vehicle" in nudge2.title


def test_nudge_cooldown_suppression():
    engine = NudgeEngine(cooldown_seconds=20.0, min_confidence_threshold=0.70)
    call_id = "test-call-nudge-cooldown"

    # Emit first signal at t=1000ms
    sig1 = SignalPayload(
        signal_id="s1",
        call_id=call_id,
        signal_type=SignalType.MISSED_CROSS_SELL,
        speaker=SpeakerRole.CUSTOMER,
        timestamp_ms=1000,
        trigger_text="I have a second car.",
        confidence=0.92,
    )
    nudge1 = engine.generate_nudge(sig1)
    assert not nudge1.suppressed

    # Emit second identical signal at t=6000ms (5 seconds later, within 20s cooldown)
    sig2 = SignalPayload(
        signal_id="s2",
        call_id=call_id,
        signal_type=SignalType.MISSED_CROSS_SELL,
        speaker=SpeakerRole.CUSTOMER,
        timestamp_ms=6000,
        trigger_text="We have another car as well.",
        confidence=0.91,
    )
    nudge2 = engine.generate_nudge(sig2)
    assert nudge2.suppressed
    assert "COOLDOWN_ACTIVE" in nudge2.suppression_reason

    # Emit third signal at t=25000ms (24 seconds after first signal, after cooldown expires)
    sig3 = SignalPayload(
        signal_id="s3",
        call_id=call_id,
        signal_type=SignalType.MISSED_CROSS_SELL,
        speaker=SpeakerRole.CUSTOMER,
        timestamp_ms=25000,
        trigger_text="Can we add the second car?",
        confidence=0.94,
    )
    nudge3 = engine.generate_nudge(sig3)
    assert not nudge3.suppressed


def test_confidence_threshold_suppression():
    engine = NudgeEngine(cooldown_seconds=20.0, min_confidence_threshold=0.70)
    call_id = "test-call-low-conf"

    sig = SignalPayload(
        signal_id="s-low",
        call_id=call_id,
        signal_type=SignalType.RISING_FRUSTRATION,
        speaker=SpeakerRole.CUSTOMER,
        timestamp_ms=1000,
        trigger_text="Hmm, I see.",
        confidence=0.55,  # Below 0.70
    )
    nudge = engine.generate_nudge(sig)
    assert nudge.suppressed
    assert "CONFIDENCE_TOO_LOW" in nudge.suppression_reason


def test_max_repeats_suppression():
    engine = NudgeEngine(cooldown_seconds=1.0, max_repeats_per_signal=2)
    call_id = "test-call-repeats"

    for i in range(2):
        sig = SignalPayload(
            signal_id=f"s-{i}",
            call_id=call_id,
            signal_type=SignalType.PAYMENT_DIFFICULTY,
            speaker=SpeakerRole.CUSTOMER,
            timestamp_ms=1000 + (i * 2000),  # 2s apart, cooldown is 1s
            trigger_text="I lost my job.",
            confidence=0.95,
        )
        ndg = engine.generate_nudge(sig)
        assert not ndg.suppressed

    # 3rd attempt exceeds max_repeats_per_signal=2
    sig3 = SignalPayload(
        signal_id="s-3",
        call_id=call_id,
        signal_type=SignalType.PAYMENT_DIFFICULTY,
        speaker=SpeakerRole.CUSTOMER,
        timestamp_ms=6000,
        trigger_text="Still no job.",
        confidence=0.95,
    )
    ndg3 = engine.generate_nudge(sig3)
    assert ndg3.suppressed
    assert "MAX_REPEATS_REACHED" in ndg3.suppression_reason
