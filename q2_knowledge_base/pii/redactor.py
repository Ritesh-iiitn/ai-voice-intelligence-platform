"""
PII Detection and Redaction Module.
Detects emails, phone numbers, national IDs (PAN, Aadhaar, SSN, TIN/SSS, NIK),
bank account numbers, and customer names. Provides masking and metadata tagging.
"""
import re
from typing import Tuple, List, Dict, Any
from q2_knowledge_base.schemas.record import DocumentRecord

class PIIDetectorRedactor:
    """Detects and redacts sensitive PII from documents prior to vector indexing."""

    PATTERNS: Dict[str, re.Pattern] = {
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        ),
        "phone": re.compile(
            r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b"
        ),
        "pan": re.compile(
            r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
        ),
        "aadhaar": re.compile(
            r"\b\d{4}\s\d{4}\s\d{4}\b"
        ),
        "ssn": re.compile(
            r"(?:\b\d{3}-\d{2}-\d{4}\b|(?:\*{3}|\d{3})-(?:\*{2}|\d{2})-\d{4})"
        ),
        "ph_tin_sss": re.compile(
            r"\b(?:\d{3}-\d{3}-\d{3}-\d{3}|\d{2}-\d{7}-\d{1})\b"
        ),
        "id_nik": re.compile(
            r"\bNIK[:\s]+[0-9]{16}\b|\b3[0-9]{15}\b"
        ),
        "bank_account": re.compile(
            r"\b(?:ACCT|ACC|IBAN|BDO|BPI|BCA|HDFC|BANK)[-:\s]+[0-9A-Z]{8,20}\b",
            re.I
        )
    }

    # Contextual name patterns
    NAME_PATTERNS = [
        re.compile(r"(?:customer_name|applicant_name|customer name|name)[:=]\s*([A-Za-z\s]{3,30})(?:,|$|\|)", re.I)
    ]

    def __init__(self):
        pass

    def analyze(self, text: str) -> Tuple[bool, List[str]]:
        """
        Analyze text for PII presence.
        Returns (contains_pii, list_of_pii_types).
        """
        if not text:
            return False, []

        detected_types = set()

        for pii_type, pattern in self.PATTERNS.items():
            if pattern.search(text):
                detected_types.add(pii_type)

        for np in self.NAME_PATTERNS:
            if np.search(text):
                detected_types.add("name")

        return len(detected_types) > 0, sorted(list(detected_types))

    def redact(self, text: str) -> str:
        """Replace detected PII instances with sanitized token masks."""
        if not text:
            return ""

        redacted = text

        # Redact specific types in sequence
        redacted = self.PATTERNS["email"].sub("[REDACTED_EMAIL]", redacted)
        redacted = self.PATTERNS["pan"].sub("[REDACTED_PAN]", redacted)
        redacted = self.PATTERNS["aadhaar"].sub("[REDACTED_AADHAAR]", redacted)
        redacted = self.PATTERNS["ssn"].sub("[REDACTED_SSN]", redacted)
        redacted = self.PATTERNS["ph_tin_sss"].sub("[REDACTED_NATIONAL_ID]", redacted)
        redacted = self.PATTERNS["id_nik"].sub("[REDACTED_NIK]", redacted)
        redacted = self.PATTERNS["bank_account"].sub("[REDACTED_BANK_ACCOUNT]", redacted)
        
        # Redact phone numbers (ensure we don't accidentally redact short dates/numbers)
        def replace_phone(match):
            val = match.group(0).strip()
            # Skip if it looks like a standard year or short amount
            if len(re.sub(r"\D", "", val)) < 7:
                return val
            return "[REDACTED_PHONE]"
        redacted = self.PATTERNS["phone"].sub(replace_phone, redacted)

        # Redact labeled names
        for np in self.NAME_PATTERNS:
            redacted = np.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_NAME]"), redacted)

        return redacted

    def process_document(self, doc: DocumentRecord, redact_content: bool = True) -> DocumentRecord:
        """Analyze and optionally redact a DocumentRecord in-place."""
        contains_pii, pii_types = self.analyze(doc.content)
        doc.contains_pii = contains_pii
        doc.pii_types = pii_types

        if contains_pii and redact_content:
            doc.content = self.redact(doc.content)

        return doc
