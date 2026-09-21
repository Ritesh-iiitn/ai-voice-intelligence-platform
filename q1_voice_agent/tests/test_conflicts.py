import pytest
from q1_voice_agent.qualification.validator import ConflictValidator
from q1_voice_agent.agent.state_machine import ConversationState

@pytest.fixture
def validator():
    return ConflictValidator()

def test_detect_conflicting_income(validator):
    state = ConversationState(monthly_income=4500.0)
    
    # Customer introduces conflicting low income
    msg = validator.check_and_update_income(state, "Actually my monthly take home is $1,800.")
    assert msg is not None
    assert "discrepancy" in msg.lower()
    assert state.unresolved_conflict is not None
    assert len(state.conflicts_detected) == 1

    # Clarification resolution
    resolved = validator.resolve_conflict(state, "Please use $4,500, my regular salary.")
    assert resolved is True
    assert state.unresolved_conflict is None
    assert state.monthly_income == 4500.0

def test_detect_conflicting_loan_amount(validator):
    state = ConversationState(requested_amount=20000.0)
    
    # Customer says they need 60k
    msg = validator.check_and_update_amount(state, "I want to borrow 60k for a truck.")
    assert msg is not None
    assert state.unresolved_conflict is not None

    # Resolve
    resolved = validator.resolve_conflict(state, "60000")
    assert resolved is True
    assert state.requested_amount == 60000.0
