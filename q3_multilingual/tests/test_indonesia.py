import pytest
from q3_multilingual.indonesia.bot import IndonesiaVoiceBot
from q3_multilingual.indonesia.terminology import (
    REGIONAL_DIALECT_FIXTURES,
    ASR_OBSERVATIONS_ID,
    parse_idr_amount
)
from q1_voice_agent.agent.state_machine import CallState

@pytest.fixture
def id_bot():
    return IndonesiaVoiceBot()

def test_id_terminology_and_asr_observations_documented():
    assert len(REGIONAL_DIALECT_FIXTURES) >= 2
    for fix in REGIONAL_DIALECT_FIXTURES:
        assert "dialect" in fix
        assert "input_phrase" in fix
        assert "asr_challenge" in fix

    assert "provider_tested" in ASR_OBSERVATIONS_ID
    assert "regional_accent_dropoff" in ASR_OBSERVATIONS_ID
    assert "mitigation_strategy" in ASR_OBSERVATIONS_ID

def test_parse_idr_amounts():
    assert parse_idr_amount("150 juta") == 150_000_000.0
    assert parse_idr_amount("25jt") == 25_000_000.0
    assert parse_idr_amount("500rb") == 500_000.0
    assert parse_idr_amount("Rp 45.000.000") == 45_000_000.0

def test_id_cooperative_flow(id_bot):
    state, greeting = id_bot.start_call("Budi Santoso")
    assert "Budi Santoso" in greeting
    assert "Apex Pembiayaan" in greeting

    # Turn 1: Confirm Identity
    out_id = id_bot.process_turn(state, "Ya, benar saya sendiri Pak.")
    assert state.current_state == CallState.CONSENT
    assert "percakapan ini kami rekam" in out_id["response"].lower()

    # Turn 2: Consent
    out_c = id_bot.process_turn(state, "Ya, bersedia silakan.")
    assert state.current_state == CallState.COLLECT_DETAILS
    assert "berapa perkiraan jumlah dana" in out_c["response"].lower()

    # Loan Amount
    out_amt = id_bot.process_turn(state, "Saya butuh pembiayaan mobil sekitar 200 juta.")
    assert state.requested_amount == 200_000_000.0
    assert "penghasilan bersih" in out_amt["response"].lower()

    # Income
    out_inc = id_bot.process_turn(state, "Gaji bulanan saya sekitar 45 juta per bulan.")
    assert state.monthly_income == 45_000_000.0

    # Credit Score
    out_score = id_bot.process_turn(state, "Skor kredit saya 750 lancar OJK.")
    assert state.current_state == CallState.RESULT
    assert "kabar gembira" in out_score["response"].lower()
    assert "LEAD-" in out_score["response"]

def test_id_consumer_finance_terminology(id_bot):
    state, _ = id_bot.start_call("Agus")
    id_bot.process_turn(state, "Ya benar.")
    
    # Customer asks about tenor and denda
    out = id_bot.process_turn(state, "Kalo mau ambil tenor 36 bulan, kena denda keterlambatan berapa ya?")
    assert "tenor fleksibel mulai dari 12 hingga 72 bulan" in out["response"].lower()
    assert "masa tenggang (grace period)" in out["response"].lower()

def test_id_regional_accent_colloquial(id_bot):
    state, _ = id_bot.start_call("Joko")
    id_bot.process_turn(state, "Ya mas.")
    
    # Javanese dialect inquiry
    out = id_bot.process_turn(state, "Nyuwun sewu mas, nek cicilan per bulane piro yo nek denda telat?")
    assert "tenor fleksibel" in out["response"].lower()
    assert "denda" in out["response"].lower()

def test_id_objection_bunga_tinggi(id_bot):
    state, _ = id_bot.start_call("Dewi")
    id_bot.process_turn(state, "Iya Dewi.")
    
    # Objection
    out = id_bot.process_turn(state, "Wah bunganya kemahalan mas, bisa kurang gak ya?")
    assert "suku bunga tetap (fixed apr)" in out["response"].lower()
    assert "bebas denda pelunasan dipercepat" in out["response"].lower()

def test_id_unsupported_fallback_stays_in_bahasa(id_bot):
    state, _ = id_bot.start_call("Hendro")
    id_bot.process_turn(state, "Iya.")
    
    # Customer asks about crypto in Indonesian
    out = id_bot.process_turn(state, "Apakah ada pinjaman jaminan koin Bitcoin dan kripto?")
    # Bot MUST stay in Indonesian and NOT switch to English!
    assert "mohon maaf, saya belum memiliki informasi resmi" in out["response"].lower()
    assert "representatif spesialis kredit kami" in out["response"].lower()

def test_id_human_escalation(id_bot):
    state, _ = id_bot.start_call("Siti Aminah")
    id_bot.process_turn(state, "Iya benar.")
    
    # Customer requests human agent
    out = id_bot.process_turn(state, "Bisa tolong bicara langsung dengan petugas manusia?")
    assert state.current_state == CallState.ESCALATION
    assert "segera menghubungkan bapak/ibu dengan representatif" in out["response"].lower()
    assert out["lead"]["qualification"] == "escalated_id"
