import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

class EscalationEvent(BaseModel):
    event_id: str
    call_id: str
    customer_name: Optional[str]
    reason: str
    trigger_phrase: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)

class EscalationDetector:
    """Detects requests for human agents and handles structured escalation dispatch."""

    ESCALATION_PATTERNS = [
        r"speak to (?:someone|a person|a human|an agent|a representative|a specialist|a manager)",
        r"talk to (?:someone|a person|a human|an agent|a representative|a specialist|a real person)",
        r"transfer me to (?:an agent|a human|someone|a representative)",
        r"give me a (?:human|real person|manager)",
        r"connect me with (?:a representative|someone|an advisor)",
        r"are you a robot",
        r"i want a human",
        r"human please"
    ]

    def __init__(self):
        self.compiled = [re.compile(p, re.I) for p in self.ESCALATION_PATTERNS]

    def check_escalation_intent(self, text: str) -> Tuple[bool, Optional[str]]:
        """Returns (is_escalation_requested, matched_phrase)."""
        for pat in self.compiled:
            match = pat.search(text)
            if match:
                return True, match.group(0)
        return False, None

    def create_escalation_event(
        self,
        call_id: str,
        customer_name: Optional[str],
        trigger_phrase: str,
        reason: str = "customer_explicit_request",
        session_details: Optional[Dict[str, Any]] = None
    ) -> EscalationEvent:
        """Create structured escalation dispatch record."""
        import uuid
        event = EscalationEvent(
            event_id=f"ESC-{uuid.uuid4().hex[:8].upper()}",
            call_id=call_id,
            customer_name=customer_name,
            reason=reason,
            trigger_phrase=trigger_phrase,
            payload=session_details or {}
        )
        return event
