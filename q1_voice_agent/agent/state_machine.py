"""
Explicit conversation state machine for outbound/inbound qualification call flows.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid

class CallState(str, Enum):
    GREETING = "GREETING"
    CONSENT = "CONSENT"
    COLLECT_DETAILS = "COLLECT_DETAILS"
    QUALIFICATION = "QUALIFICATION"
    OBJECTION_HANDLING = "OBJECTION_HANDLING"
    RESULT = "RESULT"
    ESCALATION = "ESCALATION"
    COMPLETED = "COMPLETED"

class ConversationState(BaseModel):
    """Full session state tracking customer profile, qualification criteria, and dialogue history."""
    call_id: str = Field(default_factory=lambda: f"CALL-{uuid.uuid4().hex[:8].upper()}")
    current_state: CallState = CallState.GREETING
    consent_given: Optional[bool] = None
    
    # Customer Details
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    monthly_income: Optional[float] = None
    credit_score: Optional[int] = None
    requested_amount: Optional[float] = None
    loan_purpose: Optional[str] = None  # vehicle, personal
    has_down_payment_20pct: Optional[bool] = None
    
    # Qualification & Conflict State
    qualification_status: Optional[str] = None  # qualified, preliminary_qualified, exception_review, disqualified
    qualification_reason: Optional[str] = None
    conflicts_detected: List[str] = Field(default_factory=list)
    unresolved_conflict: Optional[str] = None
    
    # Escalation & Objections
    escalation_requested: bool = False
    escalation_reason: Optional[str] = None
    objections_handled: List[str] = Field(default_factory=list)
    
    # Transcript & Citations
    dialog_turns: List[Dict[str, str]] = Field(default_factory=list)
    cited_sources: List[str] = Field(default_factory=list)

    def add_turn(self, speaker: str, text: str):
        self.dialog_turns.append({"speaker": speaker, "text": text})
