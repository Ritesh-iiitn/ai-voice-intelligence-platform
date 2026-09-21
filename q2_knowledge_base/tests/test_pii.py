import pytest
from q2_knowledge_base.pii.redactor import PIIDetectorRedactor
from q2_knowledge_base.ingestion.reader import DocumentIngestor

@pytest.fixture
def redactor():
    return PIIDetectorRedactor()

def test_detect_pii_types(redactor):
    sample_text = (
        "Customer: Johnathan Doe\n"
        "Email: john.doe@example.com\n"
        "Phone: +1-555-234-5678\n"
        "SSN: ***-**-6789\n"
        "Account: ACCT-9876543210\n"
        "PAN: ABCDE1234F\n"
    )
    has_pii, types = redactor.analyze(sample_text)
    assert has_pii is True
    assert "email" in types
    assert "phone" in types
    assert "ssn" in types
    assert "pan" in types
    assert "bank_account" in types

def test_redact_sensitive_content(redactor):
    sample_text = "Reach me at john.doe@example.com or +1-555-234-5678 for account ACCT-9876543210."
    redacted = redactor.redact(sample_text)
    assert "john.doe@example.com" not in redacted
    assert "+1-555-234-5678" not in redacted
    assert "ACCT-9876543210" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_BANK_ACCOUNT]" in redacted

def test_clean_document_has_no_pii(redactor):
    clean_policy = (
        "Tier 1 interest rate is 6.49% for credit scores above 750.\n"
        "Prepayment penalty is $0."
    )
    has_pii, types = redactor.analyze(clean_policy)
    assert has_pii is False
    assert len(types) == 0

def test_process_customer_forms_file(redactor):
    ingestor = DocumentIngestor()
    doc = ingestor.ingest_file("data/source_documents/customer_application_forms_pii.csv")
    assert doc.status == "success"
    
    processed = redactor.process_document(doc, redact_content=True)
    assert processed.contains_pii is True
    assert "email" in processed.pii_types
    assert "phone" in processed.pii_types
    assert "@finmail.ph" not in processed.content
    assert "[REDACTED_EMAIL]" in processed.content
