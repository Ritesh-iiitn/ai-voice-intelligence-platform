import pytest
from q1_voice_agent.agent.state_machine import CallState, ConversationState
from q1_voice_agent.agent.engine import VoiceAgentEngine

@pytest.fixture
def engine():
    return VoiceAgentEngine()

def test_initial_greeting_and_consent_transition(engine):
    state, greeting = engine.start_call("Jane Miller")
    assert state.current_state == CallState.GREETING
    assert "Jane Miller" in greeting

    # Turn 1: Jane affirms identity
    out = engine.process_turn(state, "Yes, this is Jane.")
    assert state.current_state == CallState.CONSENT
    assert "recorded for quality" in out["response"].lower()

    # Turn 2: Jane gives consent
    out2 = engine.process_turn(state, "Yes, that is fine.")
    assert state.current_state == CallState.COLLECT_DETAILS
    assert state.consent_given is True
    assert "funding" in out2["response"].lower() or "amount" in out2["response"].lower()

def test_consent_refusal_ends_call(engine):
    state, _ = engine.start_call("Robert Fox")
    engine.process_turn(state, "Speaking.")
    
    # Turn 2: Customer refuses recording
    out = engine.process_turn(state, "No, I do not consent to being recorded.")
    assert state.current_state == CallState.COMPLETED
    assert state.consent_given is False
    assert "cannot proceed over the phone" in out["response"].lower()
