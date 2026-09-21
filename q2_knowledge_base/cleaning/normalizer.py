"""
Terminology, date, and query normalization module.
Maps variant domain expressions into canonical schema terms for consistent indexing and retrieval.
"""
import re
from typing import Dict, List, Optional
from datetime import datetime

CANONICAL_TERMINOLOGY_MAP: Dict[str, str] = {
    # Loan Amount
    "funding amount": "requested_loan_amount",
    "requested amount": "requested_loan_amount",
    "borrowing amount": "requested_loan_amount",
    "borrowing need": "requested_loan_amount",
    "loan amount": "requested_loan_amount",
    "facility size": "requested_loan_amount",
    "principal": "requested_loan_amount",
    
    # Interest Rate & APR
    "interest rate": "annual_percentage_rate_apr",
    "apr": "annual_percentage_rate_apr",
    "annual percentage rate": "annual_percentage_rate_apr",
    "finance rate": "annual_percentage_rate_apr",
    "rate of interest": "annual_percentage_rate_apr",
    
    # Installment & Payments
    "monthly payment": "monthly_installment",
    "monthly installment": "monthly_installment",
    "installment": "monthly_installment",
    "emi": "monthly_installment",
    "angsuran": "monthly_installment",
    "cicilan": "monthly_installment",
    
    # Credit Score
    "credit score": "credit_score",
    "cibil score": "credit_score",
    "fico score": "credit_score",
    "credit rating": "credit_score",
    
    # Prepayment
    "prepayment": "prepayment_settlement",
    "early settlement": "prepayment_settlement",
    "early payoff": "prepayment_settlement",
    "foreclosure": "prepayment_settlement",
    "pay off early": "prepayment_settlement",
    
    # Down Payment
    "down payment": "down_payment",
    "dp": "down_payment",
    "initial equity": "down_payment",
    "uang muka": "down_payment",
    
    # Debt to Income
    "debt to income": "debt_to_income_ratio",
    "dti": "debt_to_income_ratio",
    "debt ratio": "debt_to_income_ratio",
    
    # Processing Fee
    "processing fee": "processing_fee",
    "origination fee": "processing_fee",
    "admin fee": "processing_fee",
    "upfront fee": "processing_fee",
    
    # Insurance Terms
    "insurance rider": "credit_protection_rider",
    "life rider": "credit_protection_rider",
    "job loss protection": "unemployment_protection",
    "involuntary unemployment": "unemployment_protection",
    "beneficiary": "policy_beneficiary",
    "grace period": "policy_grace_period",
    "lapse": "policy_lapse"
}

class TerminologyNormalizer:
    """Normalizes financial terminology, dates, amounts, and search queries."""

    def __init__(self, mapping: Optional[Dict[str, str]] = None):
        self.mapping = mapping or CANONICAL_TERMINOLOGY_MAP

    def normalize_term(self, term: str) -> str:
        """Map a phrase to its canonical form if found, else return lowered term."""
        lowered = term.strip().lower()
        return self.mapping.get(lowered, lowered)

    def normalize_query(self, query: str) -> str:
        """
        Normalize and enrich query string by appending canonical concepts
        for any matched synonyms to improve hybrid retrieval recall.
        """
        normalized_query = query.strip()
        lowered = normalized_query.lower()

        matched_canonicals = set()
        for variant, canonical in self.mapping.items():
            # Check whole word / phrase boundary
            if re.search(r"\b" + re.escape(variant) + r"\b", lowered):
                matched_canonicals.add(canonical.replace("_", " "))

        if matched_canonicals:
            enriched = f"{normalized_query} ({', '.join(sorted(matched_canonicals))})"
            return enriched
        return normalized_query

    def normalize_date(self, date_str: str) -> Optional[str]:
        """Convert various date formats to ISO YYYY-MM-DD."""
        if not date_str:
            return None
        date_str = date_str.strip()
        
        # Already YYYY-MM-DD
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str
            
        formats = [
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str

    def normalize_amount(self, amount_str: str) -> Optional[float]:
        """Convert expressions like '$25,000', '25k', 'PHP 15,000' to numeric float."""
        if not amount_str:
            return None
        clean = amount_str.strip().lower()
        
        # Check 'k' suffix
        k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", clean)
        if k_match:
            return float(k_match.group(1)) * 1000.0
            
        # Strip currency symbols and commas
        num_str = re.sub(r"[^\d.]", "", clean)
        if num_str:
            try:
                return float(num_str)
            except ValueError:
                return None
        return None
