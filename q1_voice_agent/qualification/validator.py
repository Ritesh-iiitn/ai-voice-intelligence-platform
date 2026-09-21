from __future__ import annotations
import re
from typing import Optional, Tuple, TYPE_CHECKING
from q2_knowledge_base.cleaning.normalizer import TerminologyNormalizer

if TYPE_CHECKING:
    from q1_voice_agent.agent.state_machine import ConversationState

class ConflictValidator:
    """Detects and resolves conflicting customer statements during conversation."""

    def __init__(self):
        self.normalizer = TerminologyNormalizer()

    def extract_any_amount(self, text: str) -> Optional[float]:
        """Extract a currency amount like $30,000, 30k, 2500 from text."""
        # Find pattern like $30,000 or 30k or 25000
        match = re.search(r"\$\s*([\d,]+(?:\.\d+)?)\b|(\b\d+(?:\.\d+)?\s*k\b)|(\b\d{4,6}\b)", text, re.I)
        if match:
            raw = match.group(0)
            return self.normalizer.normalize_amount(raw)
        return None

    def check_and_update_income(self, state: ConversationState, text: str) -> Optional[str]:
        """Check for income updates and detect conflicting figures."""
        is_income_utt = bool(re.search(r"(?:make|earn|income|salary|take[\s\-]*home)", text, re.I))
        is_amount_utt = bool(re.search(r"(?:borrow|loan|finance)", text, re.I))

        # Only process if this utterance is genuinely about income
        if is_income_utt or (state.requested_amount is not None and state.monthly_income is None and not is_amount_utt):
            amt = self.extract_any_amount(text)
            if amt is not None:
                # If income was already set and differs significantly (> 20% diff)
                if state.monthly_income is not None and abs(state.monthly_income - amt) / max(state.monthly_income, 1) > 0.2:
                    conflict_desc = f"income (${state.monthly_income:,.0f} vs ${amt:,.0f})"
                    state.conflicts_detected.append(conflict_desc)
                    state.unresolved_conflict = f"income:prev={state.monthly_income}:new={amt}"
                    return (
                        f"I noticed a slight discrepancy: earlier you mentioned an income of ${state.monthly_income:,.0f}, "
                        f"but just now you stated ${amt:,.0f}. Which monthly income should we use for your application?"
                    )
                state.monthly_income = amt
        return None

    def check_and_update_credit_score(self, state: ConversationState, text: str) -> Optional[str]:
        """Check for credit score updates and detect contradictory numbers."""
        # Must not be preceded by $ or comma
        match = re.search(r"(?<![\$,\d])([3-8]\d{2})(?![\d,])", text)
        if match:
            # Check context: make sure it's not a dollar amount
            surrounding = text[max(0, match.start()-10):min(len(text), match.end()+10)].lower()
            if "$" in surrounding or "dollar" in surrounding or "k" in surrounding or "salary" in surrounding:
                return None

            new_score = int(match.group(1))
            if 300 <= new_score <= 850:
                if state.credit_score is not None and abs(state.credit_score - new_score) > 30:
                    conflict_desc = f"credit score ({state.credit_score} vs {new_score})"
                    state.conflicts_detected.append(conflict_desc)
                    state.unresolved_conflict = f"credit_score:prev={state.credit_score}:new={new_score}"
                    return (
                        f"Just to clarify, earlier you noted a credit score around {state.credit_score}, "
                        f"but now mentioned {new_score}. Which score would you like us to evaluate?"
                    )
                state.credit_score = new_score
        return None

    def check_and_update_amount(self, state: ConversationState, text: str) -> Optional[str]:
        """Check for requested loan amount and detect conflicting amounts."""
        is_amount_utt = bool(re.search(r"(?:need|borrow|loan|want|looking for|finance)", text, re.I))
        if is_amount_utt or (state.requested_amount is None):
            amt = self.extract_any_amount(text)
            if amt is not None:
                if state.requested_amount is not None and abs(state.requested_amount - amt) / max(state.requested_amount, 1) > 0.3:
                    conflict_desc = f"loan amount (${state.requested_amount:,.0f} vs ${amt:,.0f})"
                    state.conflicts_detected.append(conflict_desc)
                    state.unresolved_conflict = f"amount:prev={state.requested_amount}:new={amt}"
                    return (
                        f"I want to make sure I have your numbers right: earlier we recorded ${state.requested_amount:,.0f}, "
                        f"and you just mentioned ${amt:,.0f}. What is your target financing amount?"
                    )
                state.requested_amount = amt
        return None

    def resolve_conflict(self, state: ConversationState, text: str) -> bool:
        """Handle customer clarification response to resolve conflict."""
        if not state.unresolved_conflict:
            return False

        field_type = state.unresolved_conflict.split(":")[0]
        num = self.normalizer.normalize_amount(text)

        if field_type == "income" and num:
            state.monthly_income = num
            state.unresolved_conflict = None
            return True
        elif field_type == "credit_score":
            score_match = re.search(r"\b([3-8]\d{2})\b", text)
            if score_match:
                state.credit_score = int(score_match.group(1))
                state.unresolved_conflict = None
                return True
        elif field_type == "amount" and num:
            state.requested_amount = num
            state.unresolved_conflict = None
            return True

        # If user explicitly picks the previous or new one
        if "first" in text.lower() or "earlier" in text.lower():
            state.unresolved_conflict = None
            return True
        elif "second" in text.lower() or "latter" in text.lower() or "now" in text.lower():
            # Update to new value
            val = float(state.unresolved_conflict.split("new=")[-1])
            if field_type == "income":
                state.monthly_income = val
            elif field_type == "credit_score":
                state.credit_score = int(val)
            elif field_type == "amount":
                state.requested_amount = val
            state.unresolved_conflict = None
            return True

        return False
