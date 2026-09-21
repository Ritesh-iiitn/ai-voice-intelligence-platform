# Question 1: Knowledge-Grounded Voice Agent

## Overview
The Knowledge-Grounded Voice Agent implements an automated outbound/inbound telephone dialogue system for vehicle finance and credit pre-qualification. The agent strictly grounds policy, fee, and rate answers in the Question 2 Knowledge Base with traceable citations.

## Key Features
1. **Explicit State Machine**: `GREETING` -> `CONSENT` -> `COLLECT_DETAILS` -> `QUALIFICATION` -> `OBJECTION_HANDLING` -> `RESULT` -> `ESCALATION`.
2. **Zero Hardcoded Policy Answers**: Every inquiry (e.g. APR schedules, prepayment penalties, unemployment protection) dynamically queries the hybrid retrieval engine.
3. **Traceable Citations**: Generated responses include source metadata: `[Source: ... | Section: ... | Version: ...]`.
4. **Unsupported Inquiry Fallback**: Questions outside the verified knowledge base (e.g., cryptocurrency collateral) trigger a graceful refusal and offer human escalation without hallucination.
5. **Conflict Detection & Clarification**: Contradictory statements (e.g. conflicting income or loan amounts) are detected, prompting the user for clarification before state mutation.
6. **Human Escalation**: Explicit requests ("Can I speak to someone?", "human representative") immediately stop automation and dispatch an escalation event.
7. **Mock CRM Business Action**: Creates structured leads with pre-qualification status, rate tiers, and recommended next actions (`advisor_callback`, `immediate_human_transfer`).

## Directory Layout
```
q1_voice_agent/
├── agent/            # State machine, dialog manager, escalation handler
├── qualification/    # Underwriting rules engine & conflict validator
├── prompts/          # Standardized voice script templates
├── tools/            # Mock CRM lead generation client
├── providers/        # Voice provider adapters (Mock, Deepgram, ElevenLabs)
├── recordings/       # Generated WAV audio fixtures
├── transcripts/      # Full JSON transcripts for evaluation scenarios
└── tests/            # Automated pytest test suites
```

## Running Tests and Scenarios
```bash
# Run all automated tests
pytest q1_voice_agent/tests/ -v

# Generate 5 test call scenarios and recordings
python scripts/generate_test_calls.py
```
