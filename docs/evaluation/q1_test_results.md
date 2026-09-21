# Question 1: Knowledge-Grounded Voice Agent Test Results

**Evaluation Date:** 2026-09-22

This document records the evaluation of 5 end-to-end test call scenarios testing grounding, underwriting rules, conflict resolution, unsupported question handling, and human escalation.

| Scenario ID | Scenario Name | Customer | Final State | Outcome | Citations Count | Recording |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SCENARIO-01` | Cooperative Customer (Pre-approval) | Jim Halpert | `RESULT` | **qualified** | `0` | [`recordings/scenario-01.wav`](recordings/scenario-01.wav) |
| `SCENARIO-02` | Customer Objection (Rate too high) | Dwight Schrute | `RESULT` | **qualified** | `1` | [`recordings/scenario-02.wav`](recordings/scenario-02.wav) |
| `SCENARIO-03` | Incomplete & Conflicting Financial Details | Andy Bernard | `RESULT` | **qualified** | `0` | [`recordings/scenario-03.wav`](recordings/scenario-03.wav) |
| `SCENARIO-04` | Out-of-Scope / Unsupported Question | Ryan Howard | `RESULT` | **qualified** | `1` | [`recordings/scenario-04.wav`](recordings/scenario-04.wav) |
| `SCENARIO-05` | Explicit Human Escalation | Kelly Kapoor | `ESCALATION` | **Escalated** | `0` | [`recordings/scenario-05.wav`](recordings/scenario-05.wav) |

## Detailed Scenario Breakdown

### SCENARIO-01: Cooperative Customer (Pre-approval)

- **Customer:** Jim Halpert (+1-555-019-2831)
- **Final State:** `RESULT`
- **Qualification Status:** `qualified`
- **Conflicts Detected:** `[]`
- **Escalation Triggered:** `False`
- **Created CRM Lead:** `LEAD-9DA7148C` (Action: `advisor_callback`)

#### Dialogue Transcript:
- **Agent:** Hello! This is Alex calling from Apex Credit & Vehicle Lending. I'm following up on your inquiry regarding our pre-approved auto and flexi-credit options. Am I speaking with Jim Halpert?
- **Customer:** Yes, this is Jim speaking.
- **Agent:** Great! Before we proceed to review your financing options, I want to inform you that this call is recorded for quality, compliance, and training purposes. Is it okay to continue?
- **Customer:** Yes, recording is fine, go ahead.
- **Agent:** Understood. Approximately how much funding or borrowing amount are you looking to finance?
- **Customer:** I am looking for an auto loan of about $30,000.
- **Agent:** Got it. And to check your debt-to-income eligibility, what is your approximate monthly net take-home income?
- **Customer:** My monthly net income is approximately $6,000.
- **Agent:** Thank you. Lastly, what is your approximate credit score or credit rating range?
- **Customer:** My credit score is 780.
- **Agent:** Fantastic news! Based on our underwriting guidelines, you are preliminarily qualified for Tier 1 (Excellent) with a fixed APR of 6.49% with a $0 prepayment penalty. I have generated your pre-approval reference LEAD-9DA7148C.

---

### SCENARIO-02: Customer Objection (Rate too high)

- **Customer:** Dwight Schrute (+1-555-014-9922)
- **Final State:** `RESULT`
- **Qualification Status:** `qualified`
- **Conflicts Detected:** `[]`
- **Escalation Triggered:** `False`
- **Created CRM Lead:** `LEAD-5E621E08` (Action: `advisor_callback`)

**Grounded Citations Used in Call:**
- `[Source: faq_and_objections.csv | Section: [Record 8] | Version: 1.0]`

#### Dialogue Transcript:
- **Agent:** Hello! This is Alex calling from Apex Credit & Vehicle Lending. I'm following up on your inquiry regarding our pre-approved auto and flexi-credit options. Am I speaking with Dwight Schrute?
- **Customer:** Yes, Dwight Schrute here.
- **Agent:** Great! Before we proceed to review your financing options, I want to inform you that this call is recorded for quality, compliance, and training purposes. Is it okay to continue?
- **Customer:** Yes, you have consent.
- **Agent:** Understood. Approximately how much funding or borrowing amount are you looking to finance?
- **Customer:** I need a $40,000 vehicle loan, but the interest rate feels a bit too high for me.
- **Agent:** I completely understand. Because our rates are fixed as low as 6.49% with zero prepayment penalties, you can pay down principal early to minimize interest, and there are no surprise balloon payments. Would you like to check your rate tier with a preliminary soft quote that won't impact your credit score? [Source: faq_and_objections.csv | Section: [Record 8] | Version: 1.0] Got it. And to check your debt-to-income eligibility, what is your approximate monthly net take-home income?
- **Customer:** My monthly income is $5,500.
- **Agent:** Thank you. Lastly, what is your approximate credit score or credit rating range?
- **Customer:** My credit score is 725.
- **Agent:** Fantastic news! Based on our underwriting guidelines, you are preliminarily qualified for Tier 2 (Good) with a fixed APR of 8.99% with a $0 prepayment penalty. I have generated your pre-approval reference LEAD-5E621E08.

---

### SCENARIO-03: Incomplete & Conflicting Financial Details

- **Customer:** Andy Bernard (+1-555-018-3341)
- **Final State:** `RESULT`
- **Qualification Status:** `qualified`
- **Conflicts Detected:** `['income ($20,000 vs $1,800)']`
- **Escalation Triggered:** `False`
- **Created CRM Lead:** `LEAD-A2D9FFE2` (Action: `advisor_callback`)

#### Dialogue Transcript:
- **Agent:** Hello! This is Alex calling from Apex Credit & Vehicle Lending. I'm following up on your inquiry regarding our pre-approved auto and flexi-credit options. Am I speaking with Andy Bernard?
- **Customer:** Speaking! Andy here.
- **Agent:** Great! Before we proceed to review your financing options, I want to inform you that this call is recorded for quality, compliance, and training purposes. Is it okay to continue?
- **Customer:** Sure, record away.
- **Agent:** Understood. Approximately how much funding or borrowing amount are you looking to finance?
- **Customer:** I need around $20,000.
- **Agent:** Thank you. Lastly, what is your approximate credit score or credit rating range?
- **Customer:** My take home is $1,800 a month.
- **Agent:** I noticed a slight discrepancy: earlier you mentioned an income of $20,000, but just now you stated $1,800. Which monthly income should we use for your application?
- **Customer:** Actually sorry, my take home is $5,200 including commissions.
- **Agent:** Thank you for clarifying that figure! Let's continue. Thank you. Lastly, what is your approximate credit score or credit rating range?
- **Customer:** My credit score is 690.
- **Agent:** Fantastic news! Based on our underwriting guidelines, you are preliminarily qualified for Tier 3 (Standard) with a fixed APR of 11.75% with a $0 prepayment penalty. I have generated your pre-approval reference LEAD-A2D9FFE2.

---

### SCENARIO-04: Out-of-Scope / Unsupported Question

- **Customer:** Ryan Howard (+1-555-017-7711)
- **Final State:** `RESULT`
- **Qualification Status:** `qualified`
- **Conflicts Detected:** `[]`
- **Escalation Triggered:** `False`
- **Created CRM Lead:** `LEAD-33BECED3` (Action: `advisor_callback`)

**Grounded Citations Used in Call:**
- `[Source: credit_lending_policy_v2.txt | Section: 2.1 Loan Amounts | Version: 2.1]`

#### Dialogue Transcript:
- **Agent:** Hello! This is Alex calling from Apex Credit & Vehicle Lending. I'm following up on your inquiry regarding our pre-approved auto and flexi-credit options. Am I speaking with Ryan Howard?
- **Customer:** Yes, Ryan.
- **Agent:** Great! Before we proceed to review your financing options, I want to inform you that this call is recorded for quality, compliance, and training purposes. Is it okay to continue?
- **Customer:** Fine.
- **Agent:** Understood. Approximately how much funding or borrowing amount are you looking to finance?
- **Customer:** Do you offer crypto-backed collateral loans with Bitcoin staking yields?
- **Agent:** I don't have reliable information about that in my available business policies. I would be happy to connect you with a senior lending specialist who can answer that in detail.
- **Customer:** Okay, what about regular auto loans? I need $15,000.
- **Agent:** Minimum Facility Size: $5,000. [Source: credit_lending_policy_v2.txt | Section: 2.1 Loan Amounts | Version: 2.1] Got it. And to check your debt-to-income eligibility, what is your approximate monthly net take-home income?
- **Customer:** Income is $3,800.
- **Agent:** Thank you. Lastly, what is your approximate credit score or credit rating range?
- **Customer:** Credit score 710.
- **Agent:** Fantastic news! Based on our underwriting guidelines, you are preliminarily qualified for Tier 2 (Good) with a fixed APR of 8.99% with a $0 prepayment penalty. I have generated your pre-approval reference LEAD-33BECED3.

---

### SCENARIO-05: Explicit Human Escalation

- **Customer:** Kelly Kapoor (+1-555-012-4455)
- **Final State:** `ESCALATION`
- **Qualification Status:** `None`
- **Conflicts Detected:** `[]`
- **Escalation Triggered:** `True`
- **Created CRM Lead:** `LEAD-93F847C6` (Action: `immediate_human_transfer`)

#### Dialogue Transcript:
- **Agent:** Hello! This is Alex calling from Apex Credit & Vehicle Lending. I'm following up on your inquiry regarding our pre-approved auto and flexi-credit options. Am I speaking with Kelly Kapoor?
- **Customer:** Yes, Kelly here!
- **Agent:** Great! Before we proceed to review your financing options, I want to inform you that this call is recorded for quality, compliance, and training purposes. Is it okay to continue?
- **Customer:** Can I speak to a human representative right now please? I don't want to talk to an automated system.
- **Agent:** Certainly. I am stopping the automated assessment and transferring you directly to a licensed human specialist. Please stay on the line while I connect you.

---
