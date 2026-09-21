import pytest
from q3_multilingual.philippines.bot import PhilippinesVoiceBot
from q3_multilingual.philippines.terminology import LOCALIZATION_EXAMPLES_PH, parse_php_amount
from q1_voice_agent.agent.state_machine import CallState

@pytest.fixture
def ph_bot():
    return PhilippinesVoiceBot()

def test_ph_localization_examples_documented():
    assert len(LOCALIZATION_EXAMPLES_PH) >= 3
    for ex in LOCALIZATION_EXAMPLES_PH:
        assert "domain_aspect" in ex
        assert "literal_translation" in ex
        assert "natural_taglish_localized" in ex
        assert "cultural_rationale" in ex
        assert len(ex["cultural_rationale"]) > 20

def test_parse_php_amounts():
    assert parse_php_amount("₱500,000") == 500000.0
    assert parse_php_amount("150k") == 150000.0
    assert parse_php_amount("PHP 80,000") == 80000.0

def test_ph_cooperative_flow(ph_bot):
    state, greeting = ph_bot.start_call("Maria Elena Santos")
    assert "Maria Elena Santos" in greeting
    assert "Magandang araw" in greeting

    # Turn 1: Confirm identity
    out_greet = ph_bot.process_turn(state, "Opo, ako nga po ito.")
    assert state.current_state == CallState.CONSENT
    assert "recorded po ang call" in out_greet["response"].lower()

    # Turn 2: Give consent
    out_consent = ph_bot.process_turn(state, "Opo, sige po, okay lang.")
    assert state.current_state == CallState.COLLECT_DETAILS
    assert "magkano po ang target" in out_consent["response"].lower()

    # Loan Amount
    out2 = ph_bot.process_turn(state, "Kailangan ko po ng ₱500,000 para sa kotse.")
    assert state.requested_amount == 500000.0
    assert "sweldo" in out2["response"].lower() or "kita" in out2["response"].lower()

    # Income
    out3 = ph_bot.process_turn(state, "Ang buwanang sweldo ko po ay ₱180,000.")
    assert state.monthly_income == 180000.0

    # Credit score
    out4 = ph_bot.process_turn(state, "Nasa 760 po ang credit score ko.")
    assert state.current_state == CallState.RESULT
    assert "preliminarily qualified" in out4["response"].lower()
    assert "LEAD-" in out4["response"]

def test_ph_insurance_rider_terminology(ph_bot):
    state, _ = ph_bot.start_call("Carlos Cruz")
    ph_bot.process_turn(state, "Opo.")
    
    # Customer asks about unemployment rider in Taglish
    out = ph_bot.process_turn(state, "May insurance rider po ba kayo kapag nawalan ng trabaho?")
    assert "involuntary unemployment rider" in out["response"].lower()
    assert "designated beneficiary" in out["response"].lower()

def test_ph_objection_handling(ph_bot):
    state, _ = ph_bot.start_call("Liza Soberano")
    ph_bot.process_turn(state, "Opo, go ahead.")
    
    # Customer objects to high interest
    out = ph_bot.process_turn(state, "Medyo mataas po ang interest rate ninyo eh.")
    assert "zero prepayment penalty" in out["response"].lower()
    assert "fixed po ang interest rate" in out["response"].lower()

def test_ph_unsupported_fallback_stays_in_tagalog(ph_bot):
    state, _ = ph_bot.start_call("Ferdinand")
    ph_bot.process_turn(state, "Opo.")
    
    # Customer asks about crypto in Taglish
    out = ph_bot.process_turn(state, "Nag-ooffer ba kayo ng Bitcoin collateral loan?")
    # Bot must NOT switch back to English!
    assert "wala po akong maaasahang impormasyon" in out["response"].lower()
    assert "senior lending specialist" in out["response"].lower()

def test_ph_human_escalation(ph_bot):
    state, _ = ph_bot.start_call("Gloria Macapagal")
    ph_bot.process_turn(state, "Opo.")
    
    # Customer requests human
    out = ph_bot.process_turn(state, "Gusto ko po sanang makausap ang live human agent.")
    assert state.current_state == CallState.ESCALATION
    assert "ita-transfer ko po kayo agad" in out["response"].lower()
    assert out["lead"]["qualification"] == "escalated_ph"
