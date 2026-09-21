"""
Philippines Localized Voice Agent Prototype.
Supports English, Tagalog, and natural Taglish code-switching with financial & insurance terminology.
"""
import re
from typing import Dict, Any, Optional, Tuple
from q1_voice_agent.agent.state_machine import CallState, ConversationState
from q1_voice_agent.qualification.rules import UnderwritingRulesEngine
from q1_voice_agent.tools.crm import MockCRMClient
from q3_multilingual.philippines.prompts import PH_PROMPTS
from q3_multilingual.philippines.terminology import (
    PH_FINANCIAL_TERMINOLOGY,
    LOCALIZATION_EXAMPLES_PH,
    format_php_currency,
    parse_php_amount
)

class PhilippinesVoiceBot:
    """Localized voice dialogue bot for the Philippines market."""

    def __init__(self, crm_client: Optional[MockCRMClient] = None):
        self.crm_client = crm_client or MockCRMClient()
        self.rules_engine = UnderwritingRulesEngine()

    def start_call(self, customer_name: str = "Maria Santos", phone: Optional[str] = None) -> Tuple[ConversationState, str]:
        state = ConversationState(
            customer_name=customer_name,
            phone=phone,
            current_state=CallState.GREETING
        )
        greeting = PH_PROMPTS["greeting"].format(name=customer_name)
        state.add_turn("agent", greeting)
        return state, greeting

    def process_turn(self, state: ConversationState, user_utterance: str) -> Dict[str, Any]:
        state.add_turn("customer", user_utterance)
        user_clean = user_utterance.strip().lower()

        # 1. Escalation check
        escalation_markers = ["tao", "kausap", "agent", "human", "representative", "specialist", "lipat mo", "transfer"]
        if any(m in user_clean for m in escalation_markers) and any(kw in user_clean for kw in ["gusto", "pwede", "speak", "talk", "paki"]):
            state.current_state = CallState.ESCALATION
            state.escalation_requested = True
            resp = PH_PROMPTS["escalation_transfer"]
            state.add_turn("agent", resp)
            lead = self.crm_client.create_lead(
                name=state.customer_name or "PH Customer",
                phone=state.phone,
                qualification="escalated_ph",
                reason="Customer requested human agent in Taglish",
                next_action="immediate_human_transfer"
            )
            return {"response": resp, "state": state.current_state, "lead": lead.model_dump(), "language": "taglish"}

        # 2. Unsupported topic check (crypto, etc.)
        if any(w in user_clean for w in ["crypto", "bitcoin", "staking", "nft", "forex"]):
            resp = PH_PROMPTS["unsupported_fallback"]
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "is_fallback": True, "language": "taglish"}

        # 3. Insurance Terminology / Rider Inquiries
        if any(w in user_clean for w in ["insurance", "rider", "unemployment", "mawalan ng trabaho", "beneficiary", "proteksyon", "lapse"]):
            info = PH_PROMPTS["insurance_rider_info"]
            resp = f"{info} Gusto niyo po bang ituloy natin ang inyong financing application?"
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "is_grounded": True, "language": "taglish"}

        # 4. Objection: Rate too high or general rate/prepayment inquiry
        if any(w in user_clean for w in ["mataas", "mahal", "high rate", "interest", "bigat", "fixed apr", "prepayment", "apr rate"]):
            resp = PH_PROMPTS["objection_rate_high"]
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "is_objection": True, "language": "taglish"}

        # 5. State Machine progression
        if state.current_state == CallState.GREETING:
            state.current_state = CallState.CONSENT
            resp = PH_PROMPTS["consent_request"]
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "language": "taglish"}

        elif state.current_state == CallState.CONSENT:
            if any(w in user_clean for w in ["hindi", "ayaw", "no", "wag"]):
                state.consent_given = False
                state.current_state = CallState.COMPLETED
                resp = PH_PROMPTS["consent_declined"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "language": "taglish"}
            else:
                state.consent_given = True
                state.current_state = CallState.COLLECT_DETAILS
                resp = PH_PROMPTS["ask_amount"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "language": "taglish"}

        elif state.current_state == CallState.COLLECT_DETAILS:
            amt = parse_php_amount(user_clean)
            # Update amount if not set
            if state.requested_amount is None and amt is not None:
                state.requested_amount = amt
                resp = PH_PROMPTS["ask_income"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "language": "taglish"}

            # Update income if not set
            if state.monthly_income is None and amt is not None:
                state.monthly_income = amt
                resp = PH_PROMPTS["ask_credit_score"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "language": "taglish"}

            # Update score
            score_match = re.search(r"\b([3-8]\d{2})\b", user_clean)
            if score_match:
                state.credit_score = int(score_match.group(1))

            if state.requested_amount is not None and state.monthly_income is not None and state.credit_score is not None:
                state.current_state = CallState.RESULT
                # Qualify in USD-equivalent or normalized income
                # Note: Assuming ₱55/USD conversion for income threshold test
                conv_income = state.monthly_income / 55.0 if state.monthly_income > 10000 else state.monthly_income
                mock_eval_state = state.model_copy()
                mock_eval_state.monthly_income = conv_income
                status, reason, meta = self.rules_engine.evaluate(mock_eval_state)
                state.qualification_status = status

                lead = self.crm_client.create_lead(
                    name=state.customer_name or "PH Applicant",
                    phone=state.phone,
                    requested_amount=state.requested_amount,
                    monthly_income=state.monthly_income,
                    credit_score=state.credit_score,
                    qualification=status,
                    reason=reason,
                    next_action="advisor_callback"
                )

                if status == "qualified":
                    resp = PH_PROMPTS["wrapup_qualified"].format(
                        tier_name=meta.get("tier", "Tier 1"),
                        apr=meta.get("apr", "6.49%"),
                        lead_id=lead.lead_id
                    )
                else:
                    resp = PH_PROMPTS["wrapup_disqualified"]

                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "lead": lead.model_dump(), "language": "taglish"}

            # Default prompt next missing field
            if state.requested_amount is None:
                resp = PH_PROMPTS["ask_amount"]
            elif state.monthly_income is None:
                resp = PH_PROMPTS["ask_income"]
            else:
                resp = PH_PROMPTS["ask_credit_score"]

            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "language": "taglish"}

        # Fallback completion
        resp = "Maraming salamat po sa pagtawag sa Apex Lending! Ingat po kayo lagi."
        state.add_turn("agent", resp)
        return {"response": resp, "state": state.current_state, "language": "taglish"}
