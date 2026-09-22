"""
Knowledge-grounded Voice Agent Engine.
Integrates dialog state machine, Q2 hybrid retrieval, qualification rules,
conflict resolution, human escalation, and CRM lead creation.
"""
import re
import logging
from typing import Dict, Any, Optional, List, Tuple

from q1_voice_agent.agent.state_machine import CallState, ConversationState
from q1_voice_agent.qualification.rules import UnderwritingRulesEngine
from q1_voice_agent.qualification.validator import ConflictValidator
from q1_voice_agent.agent.escalation import EscalationDetector, EscalationEvent
from q1_voice_agent.tools.crm import MockCRMClient, CRMLead
from q1_voice_agent.prompts.scripts import VOICE_SCRIPTS
from q2_knowledge_base.retrieval.hybrid import HybridRetriever
from q2_knowledge_base.retrieval.citation import CitationFormatter

logger = logging.getLogger(__name__)

class VoiceAgentEngine:
    """Enterprise knowledge-grounded voice agent dialog manager."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        crm_client: Optional[MockCRMClient] = None
    ):
        self.retriever = retriever
        self.rules_engine = UnderwritingRulesEngine()
        self.conflict_validator = ConflictValidator()
        self.escalation_detector = EscalationDetector()
        self.crm_client = crm_client or MockCRMClient()

    def start_call(self, customer_name: str = "Valued Customer", phone: Optional[str] = None) -> Tuple[ConversationState, str]:
        """Initialize a new outbound/inbound call session and generate opening greeting."""
        state = ConversationState(
            customer_name=customer_name,
            phone=phone,
            current_state=CallState.GREETING
        )
        greeting = VOICE_SCRIPTS["greeting"].format(name=customer_name)
        state.add_turn("agent", greeting)
        return state, greeting

    def process_turn(self, state: ConversationState, user_utterance: str) -> Dict[str, Any]:
        """
        Process a customer utterance, update state, perform retrieval if needed,
        and generate a grounded response.
        """
        state.add_turn("customer", user_utterance)
        user_clean = user_utterance.strip()

        # Step 1: Check for explicit human escalation intent
        is_escalation, matched_phrase = self.escalation_detector.check_escalation_intent(user_clean)
        if is_escalation:
            state.current_state = CallState.ESCALATION
            state.escalation_requested = True
            state.escalation_reason = f"Explicit customer request: '{matched_phrase}'"

            # Create escalation dispatch event
            esc_event = self.escalation_detector.create_escalation_event(
                call_id=state.call_id,
                customer_name=state.customer_name,
                trigger_phrase=matched_phrase,
                session_details=state.model_dump()
            )

            # Record in CRM
            lead = self.crm_client.create_lead(
                name=state.customer_name or "Unknown",
                phone=state.phone,
                qualification="escalated",
                reason=state.escalation_reason,
                next_action="immediate_human_transfer"
            )

            response_text = VOICE_SCRIPTS["escalation_transfer"]
            state.add_turn("agent", response_text)
            return {
                "response": response_text,
                "state": state.current_state,
                "escalation": esc_event.model_dump(),
                "lead": lead.model_dump(),
                "citations": []
            }

        # Step 2: Check for unresolved conflict clarification
        if state.unresolved_conflict:
            resolved = self.conflict_validator.resolve_conflict(state, user_clean)
            if resolved:
                ack = "Thank you for clarifying that figure! Let's continue."
                state.add_turn("agent", ack)
                # Re-evaluate next step
                return self._advance_dialog(state, prefix_msg=ack)
            else:
                retry_msg = "Could you please confirm the exact number we should use?"
                state.add_turn("agent", retry_msg)
                return {"response": retry_msg, "state": state.current_state, "citations": []}

        # Step 3: Check for unsupported out-of-scope domain keywords (crypto, bitcoin, etc.)
        unsupported_topics = ["crypto", "bitcoin", "ethereum", "staking", "blockchain", "nft", "forex"]
        if any(w in user_clean.lower() for w in unsupported_topics):
            fallback_msg = VOICE_SCRIPTS["unsupported_fallback"]
            state.add_turn("agent", fallback_msg)
            return {
                "response": fallback_msg,
                "state": state.current_state,
                "is_fallback": True,
                "citations": []
            }

        # Step 4: Check if customer is asking a Question or raising an Objection
        is_question = any(marker in user_clean.lower() for marker in [
            "?", "what", "is there", "how", "why", "do you", "can i", "rate", "fee", "penalty",
            "too high", "think about it", "already have", "unemployment", "job loss", "insurance"
        ])

        grounded_prefix = ""
        cited_records = []

        if is_question and self.retriever:
            # Query Q2 Knowledge Base
            results = self.retriever.retrieve(user_clean, top_k=2, apply_threshold=True)

            if results and results[0].score >= 0.35:
                top = results[0]
                citation_str = CitationFormatter.format_citation(top)
                state.cited_sources.append(citation_str)
                cited_records.append(top.model_dump())

                # Synthesize grounded answer excerpt
                raw_ans = self._extract_grounded_answer(top.content)
                grounded_prefix = f"{raw_ans} {citation_str} "
            elif is_question and len(user_clean.split()) >= 4:
                # Unsupported question fallback
                fallback_msg = VOICE_SCRIPTS["unsupported_fallback"]
                state.add_turn("agent", fallback_msg)
                return {
                    "response": fallback_msg,
                    "state": state.current_state,
                    "is_fallback": True,
                    "citations": []
                }

        # Step 5: Advance the state machine
        return self._advance_dialog(state, user_clean, prefix_msg=grounded_prefix, cited_records=cited_records)

    def _advance_dialog(
        self,
        state: ConversationState,
        user_clean: str = "",
        prefix_msg: str = "",
        cited_records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Advances dialog through GREETING, CONSENT, COLLECT_DETAILS, QUALIFICATION, RESULT."""
        cited = cited_records or []

        # Current State: GREETING
        if state.current_state == CallState.GREETING:
            # Affirmation of identity
            state.current_state = CallState.CONSENT
            resp = prefix_msg + VOICE_SCRIPTS["consent_request"]
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

        # Current State: CONSENT
        elif state.current_state == CallState.CONSENT:
            lowered = user_clean.lower()
            if any(w in lowered for w in ["no", "don't", "refuse", "not okay", "stop"]):
                state.consent_given = False
                state.current_state = CallState.COMPLETED
                resp = prefix_msg + VOICE_SCRIPTS["consent_declined"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "citations": state.cited_sources}
            else:
                state.consent_given = True
                state.current_state = CallState.COLLECT_DETAILS
                resp = prefix_msg + VOICE_SCRIPTS["ask_amount"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

        # Current State: COLLECT_DETAILS
        elif state.current_state == CallState.COLLECT_DETAILS:
            # Check for conflict or updates in customer utterance
            conflict_msg = (
                self.conflict_validator.check_and_update_amount(state, user_clean) or
                self.conflict_validator.check_and_update_income(state, user_clean) or
                self.conflict_validator.check_and_update_credit_score(state, user_clean)
            )

            if conflict_msg:
                resp = prefix_msg + conflict_msg
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "has_conflict": True, "citations": state.cited_sources}

            # Determine next missing piece of information
            spacing = " " if prefix_msg and not prefix_msg.endswith(" ") else ""
            if state.requested_amount is None:
                resp = prefix_msg + spacing + VOICE_SCRIPTS["ask_amount"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

            if state.monthly_income is None:
                resp = prefix_msg + spacing + VOICE_SCRIPTS["ask_income"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

            if state.credit_score is None:
                resp = prefix_msg + spacing + VOICE_SCRIPTS["ask_credit_score"]
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

            # All details present: evaluate qualification!
            state.current_state = CallState.QUALIFICATION
            return self._execute_qualification(state, prefix_msg)

        # Current State: QUALIFICATION
        elif state.current_state == CallState.QUALIFICATION:
            return self._execute_qualification(state, prefix_msg)

        # Current State: RESULT / COMPLETED
        elif state.current_state in [CallState.RESULT, CallState.COMPLETED]:
            # If the customer asks a grounded policy or information question:
            if prefix_msg:
                resp = prefix_msg.strip()
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

            # Check if customer wants to update figures
            conflict_msg = (
                self.conflict_validator.check_and_update_amount(state, user_clean) or
                self.conflict_validator.check_and_update_income(state, user_clean) or
                self.conflict_validator.check_and_update_credit_score(state, user_clean)
            )
            if conflict_msg:
                resp = prefix_msg + conflict_msg
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "has_conflict": True, "citations": state.cited_sources}

            # Closing acknowledgment
            lowered = user_clean.lower()
            if any(w in lowered for w in ["thank", "thanks", "bye", "goodbye", "ok", "okay", "done", "all good"]):
                state.current_state = CallState.COMPLETED
                resp = "You're very welcome! Thank you for speaking with Apex Lending. Have a wonderful day!"
                state.add_turn("agent", resp)
                return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

            # Default conversational follow-up
            resp = "Is there anything else I can assist you with regarding your loan application or terms?"
            state.add_turn("agent", resp)
            return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

        # Fallback completion
        resp = prefix_msg + "Thank you for speaking with Apex Lending. Have a wonderful day!"
        state.add_turn("agent", resp)
        return {"response": resp, "state": state.current_state, "citations": state.cited_sources}

    def _execute_qualification(self, state: ConversationState, prefix_msg: str = "") -> Dict[str, Any]:
        status, reason, meta = self.rules_engine.evaluate(state)
        state.qualification_status = status
        state.qualification_reason = reason
        state.current_state = CallState.RESULT

        # Create CRM Lead
        action = "advisor_callback" if status in ["qualified", "preliminary_qualified"] else "human_review"
        lead = self.crm_client.create_lead(
            name=state.customer_name or "Applicant",
            phone=state.phone,
            requested_amount=state.requested_amount,
            monthly_income=state.monthly_income,
            credit_score=state.credit_score,
            qualification=status,
            reason=reason,
            next_action=action,
            metadata=meta
        )

        if status == "qualified":
            script = VOICE_SCRIPTS["wrapup_qualified"].format(
                tier_name=meta.get("tier", "Tier 1"),
                apr=meta.get("apr", "6.49%"),
                lead_id=lead.lead_id
            )
        elif status == "exception_review":
            script = VOICE_SCRIPTS["wrapup_exception"].format(lead_id=lead.lead_id)
        elif status == "disqualified":
            script = VOICE_SCRIPTS["wrapup_disqualified"]
        else:
            script = "We still need a few details to finalize your application. Could you please share your monthly income and credit score?"
            state.current_state = CallState.COLLECT_DETAILS

        final_response = (prefix_msg + " " + script).strip()
        state.add_turn("agent", final_response)
        return {
            "response": final_response,
            "state": state.current_state,
            "qualification": status,
            "lead": lead.model_dump(),
            "citations": state.cited_sources
        }

    def _extract_grounded_answer(self, chunk_content: str) -> str:
        """Extracts the concise factual answer from the chunk text."""
        # If chunk is from CSV record, extract grounded_answer field
        match = re.search(r"grounded_answer:\s*([^|\n]+)", chunk_content)
        if match:
            return match.group(1).strip()

        # Otherwise take the first substantive policy statement
        lines = [l.strip() for l in chunk_content.splitlines() if l.strip() and not l.startswith("[") and not l.startswith("#")]
        if lines:
            return lines[0]
        return chunk_content[:200].strip()
