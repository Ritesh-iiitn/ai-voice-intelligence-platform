"""
Mock CRM lead integration tool.
Emits structured lead creation events upon qualification, escalation, or callback requests.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class CRMLead(BaseModel):
    lead_id: str = Field(default_factory=lambda: f"LEAD-{uuid.uuid4().hex[:8].upper()}")
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    requested_amount: Optional[float] = None
    monthly_income: Optional[float] = None
    credit_score: Optional[int] = None
    qualification: str  # qualified, preliminary_qualified, exception_review, disqualified, escalated
    reason: str
    next_action: str  # immediate_human_transfer, advisor_callback, automated_docs_email, credit_rehab
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MockCRMClient:
    """In-memory Mock CRM database & webhook client."""

    def __init__(self):
        self.leads: Dict[str, CRMLead] = {}

    def create_lead(
        self,
        name: str,
        qualification: str,
        reason: str,
        next_action: str = "advisor_callback",
        phone: Optional[str] = None,
        email: Optional[str] = None,
        requested_amount: Optional[float] = None,
        monthly_income: Optional[float] = None,
        credit_score: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CRMLead:
        """Create and store a structured CRM lead."""
        lead = CRMLead(
            name=name,
            phone=phone,
            email=email,
            requested_amount=requested_amount,
            monthly_income=monthly_income,
            credit_score=credit_score,
            qualification=qualification,
            reason=reason,
            next_action=next_action,
            metadata=metadata or {}
        )
        self.leads[lead.lead_id] = lead
        return lead

    def get_lead(self, lead_id: str) -> Optional[CRMLead]:
        return self.leads.get(lead_id)
