import pytest
from q2_knowledge_base.cleaning.cleaner import DocumentCleaner
from q2_knowledge_base.cleaning.normalizer import TerminologyNormalizer

@pytest.fixture
def cleaner():
    return DocumentCleaner()

@pytest.fixture
def normalizer():
    return TerminologyNormalizer()

def test_cleaner_removes_cookie_and_navigation(cleaner):
    dirty = (
        "We use cookies to improve your browsing experience. Accept cookies?\n"
        "# 1. UNDERWRITING POLICY\n"
        "Minimum score is 650.\n"
        "Navigation links: Privacy Policy | Terms of Service.\n"
        "All rights reserved.\n"
    )
    cleaned = cleaner.clean_text(dirty)
    assert "We use cookies" not in cleaned
    assert "Navigation links" not in cleaned
    assert "All rights reserved" not in cleaned
    assert "# 1. UNDERWRITING POLICY" in cleaned
    assert "Minimum score is 650." in cleaned

def test_cleaner_preserves_table_rows(cleaner):
    table_text = (
        "| Rider | Coverage | Max Benefit |\n"
        "| Unemployment | 6 installments | $3,000 |\n"
    )
    cleaned = cleaner.clean_text(table_text)
    assert "| Rider | Coverage | Max Benefit |" in cleaned
    assert "| Unemployment | 6 installments | $3,000 |" in cleaned

def test_terminology_normalization(normalizer):
    assert normalizer.normalize_term("funding amount") == "requested_loan_amount"
    assert normalizer.normalize_term("borrowing need") == "requested_loan_amount"
    assert normalizer.normalize_term("cicilan") == "monthly_installment"
    assert normalizer.normalize_term("apr") == "annual_percentage_rate_apr"

def test_query_enrichment(normalizer):
    q = "What is the interest rate for tier 1?"
    enriched = normalizer.normalize_query(q)
    assert "annual percentage rate apr" in enriched

def test_date_normalization(normalizer):
    assert normalizer.normalize_date("January 15, 2026") == "2026-01-15"
    assert normalizer.normalize_date("15/01/2026") == "2026-01-15"
    assert normalizer.normalize_date("2026-01-01") == "2026-01-01"

def test_amount_normalization(normalizer):
    assert normalizer.normalize_amount("$25,000") == 25000.0
    assert normalizer.normalize_amount("50k") == 50000.0
    assert normalizer.normalize_amount("7500.50") == 7500.50
