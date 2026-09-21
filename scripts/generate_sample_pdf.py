#!/usr/bin/env python3
"""
Generates a valid PDF file with text content for testing the PDF ingestion pipeline.
"""
import os
from pypdf import PdfWriter
from pypdf.generic import (
    DictionaryObject, NameObject, ArrayObject, NumberObject, DecodedStreamObject, create_string_object
)

def create_sample_policy_pdf(output_path: str):
    text_content = """BT /F1 12 Tf 50 750 Td (CONSUMER & VEHICLE CREDIT LENDING UNDERWRITING POLICY) Tj
0 -20 Td (Document ID: DOC-POL-LEND-2026-V2 | Version: 2.1 | Status: ACTIVE) Tj
0 -25 Td (1. PRODUCT OVERVIEW & ELIGIBILITY CRITERIA) Tj
0 -15 Td (Minimum Monthly Net Income: $2,500 per month verifiable with pay stubs.) Tj
0 -15 Td (Minimum Credit Score: 650 for standard Tier 3 underwriting.) Tj
0 -15 Td (Tier 1 APR: 6.49% for scores 750+. Tier 2 APR: 8.99% for scores 700-749.) Tj
0 -25 Td (2. LOAN TERMS AND FEES) Tj
0 -15 Td (Processing Fee: 1.5% of approved principal deducted from disbursement.) Tj
0 -15 Td (Prepayment Penalty: $0 zero penalty for early payoff.) Tj
0 -15 Td (Maximum Debt-to-Income (DTI) ratio is 45%.) Tj
0 -25 Td (3. MANDATORY DISCLOSURES) Tj
0 -15 Td (Always obtain recording consent and state the exact APR prior to agreement.) Tj
ET"""

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    
    # Add a standard Type1 font resource
    font_dict = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica")
    })
    fonts = DictionaryObject({NameObject("/F1"): font_dict})
    resources = DictionaryObject({NameObject("/Font"): fonts})
    page[NameObject("/Resources")] = resources

    # Create stream with text
    stream = DecodedStreamObject()
    stream.set_data(text_content.encode("latin1"))
    page[NameObject("/Contents")] = stream

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Sample PDF written to {output_path}")

if __name__ == "__main__":
    create_sample_policy_pdf("data/source_documents/credit_lending_policy_v2.pdf")
