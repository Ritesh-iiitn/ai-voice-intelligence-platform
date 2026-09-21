"""
Indonesia Localized Voice Agent Prototype.
Supports formal and colloquial Bahasa Indonesia, consumer finance vocabulary
(cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan), and regional accent adaptations.
"""
import re
from typing import Dict, Any, Optional, Tuple
from q1_voice_agent.agent.state_machine import CallState, ConversationState
from q1_voice_agent.qualification.rules import UnderwritingRulesEngine
from q1_voice_agent.tools.crm import MockCRMClient
from q3_multilingual.indonesia.prompts import ID_PROMPTS
from q3_multilingual.indonesia.terminology import (
    ID_FINANCIAL_TERMINOLOGY,
    REGIONAL_DIALECT_FIXTURES,
    ASR_OBSERVATIONS_ID,
    parse_idr_amount,
    format_idr_currency
)

class IndonesiaVoiceBot:
    """Localized voice dialogue bot for the Indonesian market."""

    def __init__(self, crm_client: Optional[MockCRMClient] = None):
        self.crm_client = crm_client or MockCRMClient()
        self.rules_engine = UnderwritingRulesEngine()

    def start_call(self, customer_name: str = "Budi Santoso", phone: Optional[str] = None) -> Tuple[ConversationState, str]:
        state = ConversationState(
            customer_name=customer_name,
            phone=phone,
            current_state=CallState.GREETING
        )
        greeting = ID_PROMPTS["greeting"].format(name=customer_name)
        state.add_turn("agent", greeting)
        return state, greeting

    def process_turn(self, state: ConversationState, user_utterance: str) -> Dict[str, Any]:
        state.add_turn("customer", user_utterance)
        user_clean = user_utterance.strip().lower()

        # 1. Escalation check
        escalation_markers = ["orang", "manusia", "petugas", "representatif", "cs", "operator", "bicara langsung", "hubungkan"]
        if any(m in user_clean for m in escalation_markers) and any(w in user_clean for w in ["mau", "bisa", "tolong", "bicara", "sambungkan"]):
            state.current_state = CallState.ESCALATION
            state.escalation_requested = True
            resp = ID_PROMPTS["escalation_transfer"]
            state.add_turn("agent", resp)
            lead = self.crm_client.create_lead(
                name=state.customer_name or "Nasabah ID",
                phone=state.phone,
                qualification="escalated_id",
                reason="Nasabah meminta bicara dengan representatif manusia",
                next_action="immediate_human_transfer"
            )
            return {"response": resp, "state": state.current_state, "lead": lead.model_dump(), "language": "indonesia"}

        # 2. Unsupported topic check (crypto, bitcoin, etc.)
        if any(w in user_clean for w in ["crypto", "kripto", "bitcoin", "staking", "nft", "saham"]):
            resp = ID_PROMPTS["unsupported_fallback"]
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "is_fallback": True, "language": "indonesia"}

        # 3. Consumer Finance Terminology / Tenor & Denda Inquiries
        if any(w in user_clean for w in ["tenor", "denda", "denda telat", "angsuran", "cicilan per bulane", "jatuh tempo", "lunasin cepet"]):
            info = ID_PROMPTS["tenor_dan_denda_info"]
            resp = f"{info} Apakah Bapak/Ibu ingin melanjutkan pengajuan pembiayaan ini?"
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "is_grounded": True, "language": "indonesia"}

        # 4. Objection: Bunga terlalu tinggi
        if any(w in user_clean for w in ["bunga tinggi", "bunganya kemahalan", "bisa kurang gak", "kemahalan", "berat"]):
            resp = ID_PROMPTS["objection_bunga_tinggi"]
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "is_objection": True, "language": "indonesia"}

        # 5. State Machine progression
        if state.current_state == CallState.GREETING:
            state.current_state = CallState.CONSENT
            resp = ID_PROMPTS["consent_request"]
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "language": "indonesia"}

        elif state.current_state == CallState.CONSENT:
            if any(w in user_clean for w in ["tidak", "nggak", "enggak", "jangan", "menolak"]):
                state.consent_given = False
                state.current_state = CallState.COMPLETED
                resp = ID_PROMPTS["consent_declined"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "language": "indonesia"}
            else:
                state.consent_given = True
                state.current_state = CallState.COLLECT_DETAILS
                resp = ID_PROMPTS["ask_amount"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "language": "indonesia"}

        elif state.current_state == CallState.COLLECT_DETAILS:
            amt = parse_idr_amount(user_clean)
            if state.requested_amount is None and amt is not None:
                state.requested_amount = amt
                resp = ID_PROMPTS["ask_income"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "language": "indonesia"}

            if state.monthly_income is None and amt is not None:
                state.monthly_income = amt
                resp = ID_PROMPTS["ask_credit_score"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "language": "indonesia"}

            score_match = re.search(r"\b([3-8]\d{2})\b", user_clean)
            if score_match:
                state.credit_score = int(score_match.group(1))

            if state.requested_amount is not None and state.monthly_income is not None and state.credit_score is not None:
                state.current_state = CallState.RESULT
                # Exchange rate conversion assumption for income threshold test: 1 USD ~ 15,500 IDR
                conv_income = state.monthly_income / 15500.0 if state.monthly_income > 100000 else state.monthly_income
                mock_eval_state = state.model_copy()
                mock_eval_state.monthly_income = conv_income
                status, reason, meta = self.rules_engine.evaluate(mock_eval_state)
                state.qualification_status = status

                lead = self.crm_client.create_lead(
                    name=state.customer_name or "Nasabah ID",
                    phone=state.phone,
                    requested_amount=state.requested_amount,
                    monthly_income=state.monthly_income,
                    credit_score=state.credit_score,
                    qualification=status,
                    reason=reason,
                    next_action="advisor_callback"
                )

                if status == "qualified":
                    resp = ID_PROMPTS["wrapup_qualified"].format(
                        tier_name=meta.get("tier", "Tier 1"),
                        apr=meta.get("apr", "6.49%"),
                        lead_id=lead.lead_id
                    )
                else:
                    resp = ID_PROMPTS["wrapup_disqualified"]

                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "lead": lead.model_dump(), "language": "indonesia"}

            if state.requested_amount is None:
                resp = ID_PROMPTS["ask_amount"]
            elif state.monthly_income is None:
                resp = ID_PROMPTS["ask_income"]
            else:
                resp = ID_PROMPTS["ask_credit_score"]

            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "language": "indonesia"}

        # Fallback completion
        resp = "Terima kasih telah menghubungi Apex Pembiayaan. Semoga hari Anda menyenangkan!"
        state.add_turn("agent", resp)
        return {"response": resp, "state": state.current_state, "language": "indonesia"}
