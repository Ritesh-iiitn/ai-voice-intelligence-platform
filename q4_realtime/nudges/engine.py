"""Real-time agent nudge engine with priority ranking, cooldown timers, and suppression policies."""

from __future__ import annotations

import collections
import logging
import time
from typing import Dict, List, Optional
from q4_realtime.schemas import NudgePayload, NudgePriority, SignalPayload, SignalType

logger = logging.getLogger(__name__)


class CallNudgeState:
    """Tracks suppression state, cooldowns, and emit history for a call session."""

    def __init__(self, call_id: str):
        self.call_id = call_id
        # signal_type -> timestamp_ms of last emitted (unsuppressed) nudge
        self.last_emitted_ts: Dict[SignalType, int] = {}
        # signal_type -> count of emitted nudges
        self.emit_counts: Dict[SignalType, int] = collections.defaultdict(int)
        # full log of all generated nudges (active and suppressed)
        self.nudge_history: List[NudgePayload] = []


class NudgeEngine:
    """Intelligent nudge generator with configurable cooldowns, confidence filtering, and actionable scripts."""

    def __init__(
        self,
        cooldown_seconds: float = 20.0,
        min_confidence_threshold: float = 0.70,
        max_repeats_per_signal: int = 2,
    ):
        self.cooldown_seconds = cooldown_seconds
        self.min_confidence_threshold = min_confidence_threshold
        self.max_repeats_per_signal = max_repeats_per_signal
        self._states: Dict[str, CallNudgeState] = {}
        self._latencies: List[float] = []

    def _get_state(self, call_id: str) -> CallNudgeState:
        if call_id not in self._states:
            self._states[call_id] = CallNudgeState(call_id)
        return self._states[call_id]

    def generate_nudge(self, signal: SignalPayload) -> NudgePayload:
        """Evaluate a detected signal against cooldowns and suppression rules to produce a nudge."""
        t_start = time.perf_counter()
        state = self._get_state(signal.call_id)
        current_ts = signal.timestamp_ms

        # 1. Determine base priority and content
        nudge_meta = self._resolve_nudge_metadata(signal)

        # 2. Check suppression criteria
        suppressed = False
        suppression_reason: Optional[str] = None

        # Rule A: Minimum confidence threshold
        if signal.confidence < self.min_confidence_threshold:
            suppressed = True
            suppression_reason = (
                f"CONFIDENCE_TOO_LOW ({signal.confidence:.2f} < {self.min_confidence_threshold:.2f})"
            )

        # Rule B: Max repeat limit per call
        elif state.emit_counts[signal.signal_type] >= self.max_repeats_per_signal:
            suppressed = True
            suppression_reason = (
                f"MAX_REPEATS_REACHED (already emitted {state.emit_counts[signal.signal_type]} times)"
            )

        # Rule C: Cooldown period
        elif signal.signal_type in state.last_emitted_ts:
            elapsed_sec = (current_ts - state.last_emitted_ts[signal.signal_type]) / 1000.0
            if elapsed_sec < self.cooldown_seconds:
                remaining_sec = round(self.cooldown_seconds - elapsed_sec, 1)
                suppressed = True
                suppression_reason = f"COOLDOWN_ACTIVE ({remaining_sec}s remaining)"

        # 3. Create Nudge Payload
        nudge = NudgePayload(
            nudge_id=f"ndg-{int(time.time() * 1000)}-{signal.signal_type.value[:4]}",
            call_id=signal.call_id,
            signal_type=signal.signal_type,
            priority=nudge_meta["priority"],
            title=nudge_meta["title"],
            message=nudge_meta["message"],
            recommended_script=nudge_meta["script"],
            timestamp_ms=current_ts,
            confidence=signal.confidence,
            suppressed=suppressed,
            suppression_reason=suppression_reason,
            trigger_text=signal.trigger_text,
        )

        # Update state if not suppressed
        if not suppressed:
            state.last_emitted_ts[signal.signal_type] = current_ts
            state.emit_counts[signal.signal_type] += 1

        state.nudge_history.append(nudge)

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        self._latencies.append(elapsed_ms)

        return nudge

    def _resolve_nudge_metadata(self, signal: SignalPayload) -> dict:
        """Resolve specific script and priority based on signal type and fine-grained metadata."""
        st = signal.signal_type
        meta = signal.metadata

        if st == SignalType.MISSED_CROSS_SELL:
            opp = meta.get("opportunity", "multi_vehicle_bundle")
            if opp == "loan_protection_rider":
                return {
                    "priority": NudgePriority.MEDIUM,
                    "title": "Cross-Sell: Loan Protection Insurance",
                    "message": "Customer mentioned payment protection or illness risk.",
                    "script": (
                        "By the way, we offer an optional Loan Protection Rider that covers your monthly "
                        "installments in case of temporary illness or job loss. Would you like me to include that quote?"
                    ),
                }
            return {
                "priority": NudgePriority.MEDIUM,
                "title": "Cross-Sell: Multi-Vehicle Bundle Discount",
                "message": "Customer mentioned a second car or family member vehicle.",
                "script": (
                    "By the way, did you know bundling your second vehicle qualifies you for our 15% Multi-Vehicle "
                    "Family Discount? I can calculate that bundle rate for you right now."
                ),
            }

        elif st == SignalType.COMPLIANCE_GAP:
            violation = meta.get("violation_type", "")
            if violation == "unauthorized_guarantee":
                return {
                    "priority": NudgePriority.CRITICAL,
                    "title": "MANDATORY CORRECTION: Retract Guaranteed Approval",
                    "message": "Guaranteed approval statements violate fair lending regulations.",
                    "script": (
                        "To clarify, all loan offers are contingent on complete credit underwriting and document "
                        "verification; this is an initial pre-qualification estimate only."
                    ),
                }
            elif violation == "unconsented_data_collection":
                return {
                    "priority": NudgePriority.CRITICAL,
                    "title": "COMPLIANCE NOTICE: Recording Disclosure Required",
                    "message": "Collecting sensitive PII without recorded notice violates compliance.",
                    "script": (
                        "Before we proceed with your verification details, please note this call is recorded "
                        "for quality assurance and security purposes."
                    ),
                }
            else:  # missing APR
                return {
                    "priority": NudgePriority.HIGH,
                    "title": "COMPLIANCE REMINDER: Disclose APR Terms",
                    "message": "Quoted interest rate must be accompanied by APR and underwriting terms.",
                    "script": (
                        "Please note this estimated interest rate corresponds to an estimated APR of 6.5% to 8.9%, "
                        "subject to final credit approval."
                    ),
                }

        elif st == SignalType.RISING_FRUSTRATION:
            severity = meta.get("severity", "MEDIUM")
            priority = NudgePriority.CRITICAL if severity == "HIGH" else NudgePriority.HIGH
            return {
                "priority": priority,
                "title": "De-escalation & Supervisor Transfer Option",
                "message": "Customer sentiment is declining. Validate emotions and offer human transfer.",
                "script": (
                    "I sincerely apologize for the frustration and repetition. Let me take care of this directly, "
                    "or if you prefer, I can transfer you immediately to a senior supervisor."
                ),
            }

        elif st == SignalType.PAYMENT_DIFFICULTY:
            category = meta.get("hardship_category", "liquidity_shortage")
            if category == "medical_crisis":
                return {
                    "priority": NudgePriority.HIGH,
                    "title": "Hardship Relief: Medical Emergency Assistance",
                    "message": "Customer cited hospital/medical hardship. Inform about loan protection claims.",
                    "script": (
                        "I am so sorry to hear about your medical emergency. If you have our payment protection rider, "
                        "your installments may be covered. We can also grant an immediate 30-day grace period."
                    ),
                }
            return {
                "priority": NudgePriority.HIGH,
                "title": "Hardship Relief: Deferral & Restructuring Program",
                "message": "Customer cited job loss or inability to pay. Offer hardship relief program.",
                "script": (
                    "We understand unexpected financial challenges happen. We offer temporary payment deferrals and "
                    "term extensions to help you bridge this period. Would you like to review our hardship plan?"
                ),
            }

        return {
            "priority": NudgePriority.LOW,
            "title": "Agent Assistance Notice",
            "message": "General conversational recommendation.",
            "script": "How else may I assist you with your account today?",
        }

    def get_call_nudges(
        self, call_id: str, include_suppressed: bool = False
    ) -> List[NudgePayload]:
        """Retrieve historical nudges generated for this call."""
        state = self._get_state(call_id)
        if include_suppressed:
            return list(state.nudge_history)
        return [n for n in state.nudge_history if not n.suppressed]

    def get_latency_stats(self) -> Dict[str, float]:
        """Compute latency distribution for nudge generation."""
        if not self._latencies:
            return {"mean_ms": 0.0, "p95_ms": 0.0, "count": 0}

        sorted_lat = sorted(self._latencies)
        p95_idx = int(0.95 * len(sorted_lat))
        return {
            "mean_ms": round(sum(self._latencies) / len(self._latencies), 3),
            "p95_ms": round(sorted_lat[min(p95_idx, len(sorted_lat) - 1)], 3),
            "count": len(self._latencies),
        }

    def reset_call(self, call_id: str) -> None:
        """Clear memory state for call."""
        self._states.pop(call_id, None)


# Global singleton
_engine: Optional[NudgeEngine] = None


def get_nudge_engine() -> NudgeEngine:
    """Retrieve or initialize global NudgeEngine singleton."""
    global _engine
    if _engine is None:
        _engine = NudgeEngine()
    return _engine
