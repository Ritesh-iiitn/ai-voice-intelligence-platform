# Question 2: Knowledge Base Retrieval Evaluation Report

**Evaluation Date:** 2026-09-22

**Pipeline:** Multi-format Ingestion -> Cleaning & PII Masking -> Semantic Chunking -> Local Dense TF-IDF + BM25 Hybrid Retrieval

**Summary Metrics:**

- **Mean Reciprocal Rank (MRR):** `0.917`
- **Mean Precision@3:** `0.556`
- **Total Benchmark Queries:** `6`

| Metric | Value |
| :--- | :--- |
| Correct | 5 (83.3%) |
| Partially Correct | 1 (16.7%) |
| Incorrect | 0 (0.0%) |
| MRR Score | 0.917 |
| Mean Precision@3 | 0.556 |

## Detailed Query Benchmark Results

### Query `Q2-EVAL-01`: What is the fixed APR interest rate for someone with a credit score of 760?

- **Expected Information:** Tier 1 APR is 6.49% for credit scores 750+
- **Verdict:** `CORRECT` (RR: `1.0`, P@3: `0.667`)
- **Explanation:** Top-ranked chunk directly matched verified policy source and facts.

#### Retrieved Top Records:
1. **faq_and_objections_chk_002** (Score: `0.6473`, Mode: `hybrid`)
   - Citation: `[Source: faq_and_objections.csv | Section: [Record 3] | Version: 1.0]`
   - Content: *"[faq_and_objections.csv > [Record 3]] [Record 3] faq_id: FAQ-003 | category: rates | question: What interest rate (APR) will I get on my loa..."*
2. **credit_lending_policy_v1_chk_003** (Score: `0.4551`, Mode: `hybrid`)
   - Citation: `[Source: credit_lending_policy_v1.txt | Section: 1.2 Credit Score Tiers & APR Schedules | Version: 1.0]`
   - Content: *"[CONSUMER CREDIT LENDING POLICY (SUPERSEDED) > 1.2 Credit Score Tiers & APR Schedules] Tier 1 (Score 750+): Fixed APR of 7.99% p.a. - Tier 2..."*
3. **faq_and_objections_chk_007** (Score: `0.4392`, Mode: `hybrid`)
   - Citation: `[Source: faq_and_objections.csv | Section: [Record 8] | Version: 1.0]`
   - Content: *"[faq_and_objections.csv > [Record 8]] [Record 8] faq_id: OBJ-001 | category: objection | question: The interest rate feels a bit too high fo..."*

---

### Query `Q2-EVAL-02`: Will I be penalized if I pay off my auto loan balance early?

- **Expected Information:** $0 prepayment penalty; borrowers may settle full balance anytime without penalty
- **Verdict:** `CORRECT` (RR: `1.0`, P@3: `0.333`)
- **Explanation:** Top-ranked chunk directly matched verified policy source and facts.

#### Retrieved Top Records:
1. **faq_and_objections_chk_001** (Score: `0.5782`, Mode: `hybrid`)
   - Citation: `[Source: faq_and_objections.csv | Section: [Record 2] | Version: 1.0]`
   - Content: *"[faq_and_objections.csv > [Record 2]] [Record 2] faq_id: FAQ-002 | category: prepayment | question: Can I pay off my loan early without pena..."*
2. **insurance_protection_riders_chk_002** (Score: `0.4055`, Mode: `hybrid`)
   - Citation: `[Source: insurance_protection_riders.html | Section: 2. Protection Coverage Table | Version: 1.4]`
   - Content: *"[Credit Protection & Life Insurance Riders - Policy Terms > 2. Protection Coverage Table] Rider Option | Coverage Scope | Maximum Benefit | ..."*

---

### Query `Q2-EVAL-03`: What is the minimum monthly net income required to be eligible?

- **Expected Information:** Minimum net monthly income of $2,500 supported by pay slips or bank statements
- **Verdict:** `PARTIALLY_CORRECT` (RR: `0.5`, P@3: `0.667`)
- **Explanation:** Relevant information retrieved at rank #2.

#### Retrieved Top Records:
1. **credit_lending_policy_v1_chk_002** (Score: `0.581`, Mode: `hybrid`)
   - Citation: `[Source: credit_lending_policy_v1.txt | Section: 1.1 General Eligibility Requirements | Version: 1.0]`
   - Content: *"[CONSUMER CREDIT LENDING POLICY (SUPERSEDED) > 1.1 General Eligibility Requirements] Age: Applicant must be between 23 and 60 years old at m..."*
2. **faq_and_objections_chk_003** (Score: `0.5334`, Mode: `hybrid`)
   - Citation: `[Source: faq_and_objections.csv | Section: [Record 4] | Version: 1.0]`
   - Content: *"[faq_and_objections.csv > [Record 4]] [Record 4] faq_id: FAQ-004 | category: eligibility | question: What is the minimum income needed to qu..."*
3. **credit_lending_policy_v2_chk_001** (Score: `0.5301`, Mode: `hybrid`)
   - Citation: `[Source: credit_lending_policy_v2.pdf | Section: 1. PRODUCT OVERVIEW & ELIGIBILITY CRITERIA | Version: 2.1]`
   - Content: *"[CONSUMER & VEHICLE CREDIT LENDING UNDERWRITING POLICY > 1. PRODUCT OVERVIEW & ELIGIBILITY CRITERIA] Minimum Monthly Net Income: $2,500 per ..."*

---

### Query `Q2-EVAL-04`: What protection is provided if I lose my job unexpectedly?

- **Expected Information:** Involuntary Unemployment Rider covers up to 6 monthly installments (up to $3,000/month)
- **Verdict:** `CORRECT` (RR: `1.0`, P@3: `0.333`)
- **Explanation:** Top-ranked chunk directly matched verified policy source and facts.

#### Retrieved Top Records:
1. **faq_and_objections_chk_005** (Score: `0.5891`, Mode: `hybrid`)
   - Citation: `[Source: faq_and_objections.csv | Section: [Record 6] | Version: 1.0]`
   - Content: *"[faq_and_objections.csv > [Record 6]] [Record 6] faq_id: FAQ-006 | category: insurance | question: What happens if I lose my job during the ..."*
2. **insurance_protection_riders_chk_001** (Score: `0.3623`, Mode: `hybrid`)
   - Citation: `[Source: insurance_protection_riders.html | Section: 1. Rider Overview & Product Scope | Version: 1.4]`
   - Content: *"[Credit Protection & Life Insurance Riders - Policy Terms > 1. Rider Overview & Product Scope] The Credit Protection and Debt Cancellation R..."*

---

### Query `Q2-EVAL-05`: Is there a discount for protecting multiple household vehicles?

- **Expected Information:** Multi-Vehicle Household Bundle provides 15% discount on combined protection premiums
- **Verdict:** `CORRECT` (RR: `1.0`, P@3: `0.333`)
- **Explanation:** Top-ranked chunk directly matched verified policy source and facts.

#### Retrieved Top Records:
1. **insurance_protection_riders_chk_002** (Score: `0.5377`, Mode: `hybrid`)
   - Citation: `[Source: insurance_protection_riders.html | Section: 2. Protection Coverage Table | Version: 1.4]`
   - Content: *"[Credit Protection & Life Insurance Riders - Policy Terms > 2. Protection Coverage Table] Rider Option | Coverage Scope | Maximum Benefit | ..."*

---

### Query `Q2-EVAL-06`: Do you offer crypto-backed collateral loans with Bitcoin staking yields?

- **Expected Information:** Out of scope. No policy records exist for cryptocurrency or staking.
- **Verdict:** `CORRECT` (RR: `1.0`, P@3: `1.0`)
- **Explanation:** Query has no facts in KB; zero hallucinated facts retrieved, enabling safe fallback.

#### Retrieved Top Records:
1. **credit_lending_policy_v2_chk_004** (Score: `0.5924`, Mode: `hybrid`)
   - Citation: `[Source: credit_lending_policy_v2.txt | Section: 2.1 Loan Amounts | Version: 2.1]`
   - Content: *"[CONSUMER & VEHICLE CREDIT LENDING UNDERWRITING POLICY > 2.1 Loan Amounts] Minimum Facility Size: $5,000. - Maximum Facility Size: $75,000 f..."*
2. **credit_lending_policy_v2_chk_001** (Score: `0.4126`, Mode: `hybrid`)
   - Citation: `[Source: credit_lending_policy_v2.txt | Section: 1. PRODUCT OVERVIEW & ELIGIBILITY CRITERIA | Version: 2.1]`
   - Content: *"[CONSUMER & VEHICLE CREDIT LENDING UNDERWRITING POLICY > 1. PRODUCT OVERVIEW & ELIGIBILITY CRITERIA] The Consumer & Vehicle Flexi-Credit fac..."*
3. **credit_lending_policy_v2_chk_009** (Score: `0.3375`, Mode: `hybrid`)
   - Citation: `[Source: credit_lending_policy_v2.txt | Section: 4. EXCEPTION POLICIES & SPECIAL APPROVALS | Version: 2.1]`
   - Content: *"[CONSUMER & VEHICLE CREDIT LENDING UNDERWRITING POLICY > 4. EXCEPTION POLICIES & SPECIAL APPROVALS] Near-Prime Exception: Applicants with cr..."*

---
