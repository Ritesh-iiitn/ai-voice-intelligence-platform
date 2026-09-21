import pytest
from pathlib import Path
from q2_knowledge_base.ingestion.reader import DocumentIngestor

@pytest.fixture
def ingestor():
    return DocumentIngestor()

def test_ingest_txt(ingestor):
    doc = ingestor.ingest_file("data/source_documents/credit_lending_policy_v2.txt")
    assert doc.status == "success"
    assert doc.source_type == "txt"
    assert "2.1" in doc.version
    assert "CONSUMER & VEHICLE CREDIT LENDING" in doc.title.upper()
    assert "6.49%" in doc.content
    assert doc.effective_date == "2026-01-01"

def test_ingest_pdf(ingestor):
    doc = ingestor.ingest_file("data/source_documents/credit_lending_policy_v2.pdf")
    assert doc.status == "success"
    assert doc.source_type == "pdf"
    assert "CONSUMER & VEHICLE CREDIT LENDING" in doc.content
    assert "$2,500" in doc.content

def test_ingest_html_strips_boilerplate(ingestor):
    doc = ingestor.ingest_file("data/source_documents/insurance_protection_riders.html")
    assert doc.status == "success"
    assert doc.source_type == "html"
    assert "Accept cookies" not in doc.content
    assert "Home | About Us | Contact" not in doc.content
    # Preserves table content
    assert "Involuntary Unemployment Protection" in doc.content
    assert "Total & Permanent Disability (TPD)" in doc.content
    assert "Multi-Vehicle Household Bundle" in doc.content

def test_ingest_csv(ingestor):
    doc = ingestor.ingest_file("data/source_documents/faq_and_objections.csv")
    assert doc.status == "success"
    assert doc.source_type == "csv"
    assert "FAQ-001" in doc.content
    assert "prepayment" in doc.content.lower()

def test_ingest_nonexistent_file(ingestor):
    doc = ingestor.ingest_file("data/source_documents/does_not_exist.pdf")
    assert doc.status == "failed"
    assert "File not found" in doc.error_message
    assert doc.content == ""

def test_ingest_empty_file(ingestor, tmp_path):
    empty_file = tmp_path / "empty_doc.txt"
    empty_file.write_text("")
    doc = ingestor.ingest_file(str(empty_file))
    assert doc.status == "empty"
    assert "empty" in doc.error_message.lower()
