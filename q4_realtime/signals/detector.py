"""Real-time signal detection engine for compliance, revenue opportunities, sentiment, and credit risk."""

from __future__ import annotations

import collections
import logging
import re
import time
from typing import Dict, List, Optional
from q4_realtime.schemas import SignalPayload, SignalType, SpeakerRole, TranscriptChunk

logger = logging.getLogger(__name__)


class CallContext:
    """Tracks state and conversational history for a single call session."""

    def __init__(self, call_id: str):
        self.call_id = call_id
        self.history: List[TranscriptChunk] = []
        self.consent_given: bool = False
        self.recording_disclosed: bool = False
        self.apr_disclosed: bool = False
        self.cross_sell_candidate_active: bool = False
        self.cross_sell_offered: bool = False
        self.frustration_counter: int = 0
        self.detected_signals: List[SignalPayload] = []


class SignalDetector:
    """Real-time rule- and pattern-based conversational signal detector with sub-second latency."""

    def __init__(self):
        self._contexts: Dict[str, CallContext] = collections.defaultdict(CallContext)
        self._latencies: List[float] = []

        # Compile high-performance regex patterns
        self._re_recording_consent = re.compile(
            r"\b(call is recorded|monitored for quality|recording this call|consent to be recorded)\b",
            re.IGNORECASE,
        )
        self._re_rate_quote = re.compile(
            r"\b(interest rate of \d+(\.\d+)?%|\d+(\.\d+)?% interest|rate is \d+(\.\d+)?%|rate will be \d+(\.\d+)?%|monthly payment of \$\d+)\b",
            re.IGNORECASE,
        )
        self._re_apr_disclosure = re.compile(
            r"\b(apr|annual percentage rate|subject to credit approval|terms and conditions apply)\b",
            re.IGNORECASE,
        )
        self._re_guarantee_promise = re.compile(
            r"\b(guaranteed approval|100% approved|no credit check required|definitely approved without qualification)\b",
            re.IGNORECASE,
        )
        self._re_sensitive_request = re.compile(
            r"\b(social security number|ssn|bank account number|nik|ktp|tin)\b",
            re.IGNORECASE,
        )

        # Cross-sell patterns
        self._re_cross_sell_triggers = re.compile(
            r"\b(second (car|vehicle)|another (car|vehicle)|wife'?s? (car|vehicle)|husband'?s? (car|vehicle)|spouse'?s? (car|vehicle)|daughter'?s? (car|vehicle)|son'?s? (car|vehicle)|family car|two cars|multiple vehicles|gap insurance|loan protection|protect my payments|life insurance rider)\b",
            re.IGNORECASE,
        )
        self._re_cross_sell_offers = re.compile(
            r"\b(multi-vehicle|bundle discount|loan protection|add insurance|gap coverage|family discount)\b",
            re.IGNORECASE,
        )

        # Frustration patterns
        self._re_frustration_severe = re.compile(
            r"\b(speak to a human|talk to a (real )?person|transfer me to (a )?supervisor|transfer me to (a )?manager|live representative|i asked you (two|three|several) times|i already told you|stop repeating|this is ridiculous|waste of time|useless robot|terrible service|horrible|furious|unacceptable)\b",
            re.IGNORECASE,
        )
        self._re_frustration_mild = re.compile(
            r"\b(annoying|frustrated|confused|not answering my question|does not make sense|don't understand why)\b",
            re.IGNORECASE,
        )

        # Payment difficulty patterns
        self._re_hardship_employment = re.compile(
            r"\b(lost my job|laid off|job loss|unemployed|hours (got )?cut|furloughed|downsized|no income right now|lost my business)\b",
            re.IGNORECASE,
        )
        self._re_hardship_medical = re.compile(
            r"\b(hospital (bills|expenses)|medical emergency|surgery|in the hospital|family illness|medical crisis)\b",
            re.IGNORECASE,
        )
        self._re_hardship_payment = re.compile(
            r"\b(can'?t afford (this|the) payment|cannot pay (this|my) (month|installment|bill)|need an extension|grace period|pay late|skip a payment|hardship assistance|struggling financially|behind on payments|financial trouble)\b",
            re.IGNORECASE,
        )

    def _get_context(self, call_id: str) -> CallContext:
        if call_id not in self._contexts:
            self._contexts[call_id] = CallContext(call_id)
        return self._contexts[call_id]

    async def analyze_chunk(self, chunk: TranscriptChunk) -> List[SignalPayload]:
        """Analyze an incoming transcript segment in real-time and return any detected signals."""
        t_start = time.perf_counter()
        ctx = self._get_context(chunk.call_id)
        ctx.history.append(chunk)

        signals: List[SignalPayload] = []

        # Update running state
        text = chunk.text
        if chunk.speaker == SpeakerRole.AGENT:
            if self._re_recording_consent.search(text):
                ctx.recording_disclosed = True
            if self._re_apr_disclosure.search(text):
                ctx.apr_disclosed = True
            if self._re_cross_sell_offers.search(text):
                ctx.cross_sell_offered = True

        # Check for 4 signal categories
        sig_cross_sell = self._check_missed_cross_sell(chunk, ctx)
        if sig_cross_sell:
            signals.append(sig_cross_sell)

        sig_compliance = self._check_compliance_gap(chunk, ctx)
        if sig_compliance:
            signals.append(sig_compliance)

        sig_frustration = self._check_rising_frustration(chunk, ctx)
        if sig_frustration:
            signals.append(sig_frustration)

        sig_payment = self._check_payment_difficulty(chunk, ctx)
        if sig_payment:
            signals.append(sig_payment)

        # Track latency
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        self._latencies.append(elapsed_ms)

        for s in signals:
            ctx.detected_signals.append(s)

        return signals

    def _check_missed_cross_sell(
        self, chunk: TranscriptChunk, ctx: CallContext
    ) -> Optional[SignalPayload]:
        """Detect cross-sell opportunities mentioned by customer that agent hasn't pitched."""
        if chunk.speaker != SpeakerRole.CUSTOMER:
            return None

        match = self._re_cross_sell_triggers.search(chunk.text)
        if match:
            ctx.cross_sell_candidate_active = True
            trigger_term = match.group(0)
            return SignalPayload(
                signal_id=f"sig-cross-{int(time.time() * 1000)}",
                call_id=chunk.call_id,
                signal_type=SignalType.MISSED_CROSS_SELL,
                speaker=chunk.speaker,
                timestamp_ms=chunk.timestamp_ms,
                trigger_text=chunk.text,
                confidence=0.92,
                metadata={
                    "matched_trigger": trigger_term,
                    "opportunity": "multi_vehicle_bundle" if "car" in trigger_term or "vehicle" in trigger_term else "loan_protection_rider",
                },
            )
        return None

    def _check_compliance_gap(
        self, chunk: TranscriptChunk, ctx: CallContext
    ) -> Optional[SignalPayload]:
        """Detect compliance non-adherence by the agent (unauthorized guarantees, missing APR, missing consent)."""
        if chunk.speaker != SpeakerRole.AGENT:
            return None

        # Check 1: Unauthorized Guarantee
        guarantee_match = self._re_guarantee_promise.search(chunk.text)
        if guarantee_match:
            return SignalPayload(
                signal_id=f"sig-comp-{int(time.time() * 1000)}",
                call_id=chunk.call_id,
                signal_type=SignalType.COMPLIANCE_GAP,
                speaker=chunk.speaker,
                timestamp_ms=chunk.timestamp_ms,
                trigger_text=chunk.text,
                confidence=0.98,
                metadata={
                    "violation_type": "unauthorized_guarantee",
                    "matched_phrase": guarantee_match.group(0),
                    "action_required": "Correct statement immediately; clarify pre-qualification only",
                },
            )

        # Check 2: Rate quote without APR disclosure
        rate_match = self._re_rate_quote.search(chunk.text)
        if rate_match and not ctx.apr_disclosed:
            return SignalPayload(
                signal_id=f"sig-comp-{int(time.time() * 1000)}",
                call_id=chunk.call_id,
                signal_type=SignalType.COMPLIANCE_GAP,
                speaker=chunk.speaker,
                timestamp_ms=chunk.timestamp_ms,
                trigger_text=chunk.text,
                confidence=0.90,
                metadata={
                    "violation_type": "missing_apr_disclosure",
                    "matched_phrase": rate_match.group(0),
                    "action_required": "Must disclose APR and credit approval contingency",
                },
            )

        # Check 3: Sensitive data collection without recording disclosure
        sensitive_match = self._re_sensitive_request.search(chunk.text)
        if sensitive_match and not ctx.recording_disclosed:
            return SignalPayload(
                signal_id=f"sig-comp-{int(time.time() * 1000)}",
                call_id=chunk.call_id,
                signal_type=SignalType.COMPLIANCE_GAP,
                speaker=chunk.speaker,
                timestamp_ms=chunk.timestamp_ms,
                trigger_text=chunk.text,
                confidence=0.94,
                metadata={
                    "violation_type": "unconsented_data_collection",
                    "matched_phrase": sensitive_match.group(0),
                    "action_required": "Provide mandatory recording notice before collecting PII",
                },
            )

        return None

    def _check_rising_frustration(
        self, chunk: TranscriptChunk, ctx: CallContext
    ) -> Optional[SignalPayload]:
        """Detect escalating customer frustration or transfer demands."""
        if chunk.speaker != SpeakerRole.CUSTOMER:
            return None

        severe_match = self._re_frustration_severe.search(chunk.text)
        if severe_match:
            ctx.frustration_counter += 2
            return SignalPayload(
                signal_id=f"sig-frust-{int(time.time() * 1000)}",
                call_id=chunk.call_id,
                signal_type=SignalType.RISING_FRUSTRATION,
                speaker=chunk.speaker,
                timestamp_ms=chunk.timestamp_ms,
                trigger_text=chunk.text,
                confidence=0.95,
                metadata={
                    "severity": "HIGH",
                    "matched_phrase": severe_match.group(0),
                    "frustration_score": ctx.frustration_counter,
                },
            )

        mild_match = self._re_frustration_mild.search(chunk.text)
        if mild_match:
            ctx.frustration_counter += 1
            if ctx.frustration_counter >= 2:
                return SignalPayload(
                    signal_id=f"sig-frust-{int(time.time() * 1000)}",
                    call_id=chunk.call_id,
                    signal_type=SignalType.RISING_FRUSTRATION,
                    speaker=chunk.speaker,
                    timestamp_ms=chunk.timestamp_ms,
                    trigger_text=chunk.text,
                    confidence=0.82,
                    metadata={
                        "severity": "MEDIUM",
                        "matched_phrase": mild_match.group(0),
                        "frustration_score": ctx.frustration_counter,
                    },
                )

        return None

    def _check_payment_difficulty(
        self, chunk: TranscriptChunk, ctx: CallContext
    ) -> Optional[SignalPayload]:
        """Detect borrower financial hardship, delinquency risk, or deferral requests."""
        if chunk.speaker != SpeakerRole.CUSTOMER:
            return None

        emp_match = self._re_hardship_employment.search(chunk.text)
        if emp_match:
            return SignalPayload(
                signal_id=f"sig-pay-{int(time.time() * 1000)}",
                call_id=chunk.call_id,
                signal_type=SignalType.PAYMENT_DIFFICULTY,
                speaker=chunk.speaker,
                timestamp_ms=chunk.timestamp_ms,
                trigger_text=chunk.text,
                confidence=0.96,
                metadata={
                    "hardship_category": "employment_loss",
                    "matched_phrase": emp_match.group(0),
                    "recommended_action": "route_to_hardship_concession_program",
                },
            )

        med_match = self._re_hardship_medical.search(chunk.text)
        if med_match:
            return SignalPayload(
                signal_id=f"sig-pay-{int(time.time() * 1000)}",
                call_id=chunk.call_id,
                signal_type=SignalType.PAYMENT_DIFFICULTY,
                speaker=chunk.speaker,
                timestamp_ms=chunk.timestamp_ms,
                trigger_text=chunk.text,
                confidence=0.92,
                metadata={
                    "hardship_category": "medical_crisis",
                    "matched_phrase": med_match.group(0),
                    "recommended_action": "check_loan_protection_policy_claim",
                },
            )

        pay_match = self._re_hardship_payment.search(chunk.text)
        if pay_match:
            return SignalPayload(
                signal_id=f"sig-pay-{int(time.time() * 1000)}",
                call_id=chunk.call_id,
                signal_type=SignalType.PAYMENT_DIFFICULTY,
                speaker=chunk.speaker,
                timestamp_ms=chunk.timestamp_ms,
                trigger_text=chunk.text,
                confidence=0.94,
                metadata={
                    "hardship_category": "liquidity_shortage",
                    "matched_phrase": pay_match.group(0),
                    "recommended_action": "discuss_grace_period_and_restructuring",
                },
            )

        return None

    def get_latency_stats(self) -> Dict[str, float]:
        """Compute latency distribution for signal analysis."""
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
        self._contexts.pop(call_id, None)


# Global singleton
_detector: Optional[SignalDetector] = None


def get_signal_detector() -> SignalDetector:
    """Retrieve or initialize the global SignalDetector singleton."""
    global _detector
    if _detector is None:
        _detector = SignalDetector()
    return _detector
