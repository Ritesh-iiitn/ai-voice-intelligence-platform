import pytest
from q1_voice_agent.qualification.rules import UnderwritingRulesEngine
from q1_voice_agent.agent.state_machine import ConversationState

@pytest.fixture
def rules():
    return UnderwritingRulesEngine()

def test_tier_1_qualification(rules):
    state = ConversationState(
        customer_name="Alice",
        monthly_income=5000.0,
        credit_score=760,
        requested_amount=25000.0
    )
    status, reason, meta = rules.evaluate(state)
    assert status == "qualified"
    assert "Tier 1" in meta["tier"]
    assert meta["apr"] == "6.49%"

def test_tier_3_qualification(rules):
    state = ConversationState(
        customer_name="Bob",
        monthly_income=3200.0,
        credit_score=670,
        requested_amount=15000.0
    )
    status, reason, meta = rules.evaluate(state)
    assert status == "qualified"
    assert "Tier 3" in meta["tier"]
    assert meta["apr"] == "11.75%"

def test_near_prime_exception(rules):
    state = ConversationState(
        customer_name="Charlie",
        monthly_income=4000.0,
        credit_score=635,
        requested_amount=18000.0
    )
    status, reason, meta = rules.evaluate(state)
    assert status == "exception_review"
    assert meta.get("requires_down_payment") is True

def test_income_disqualification(rules):
    state = ConversationState(
        customer_name="Dave",
        monthly_income=1800.0,  # Below $2,500
        credit_score=720,
        requested_amount=10000.0
    )
    status, reason, meta = rules.evaluate(state)
    assert status == "disqualified"
    assert meta.get("reason_code") == "INSUFFICIENT_INCOME"
