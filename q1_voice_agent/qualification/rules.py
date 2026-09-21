from __future__ import annotations
from typing import Tuple, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from q1_voice_agent.agent.state_machine import ConversationState

class UnderwritingRulesEngine:
    """Evaluates customer credit and income against official lending guidelines."""

    MIN_INCOME: float = 2500.0
    MIN_CREDIT_SCORE: int = 650
    EXCEPTION_MIN_SCORE: int = 620
    MIN_LOAN_AMOUNT: float = 5000.0
    MAX_LOAN_AMOUNT: float = 75000.0

    TIER_RATES = {
        "Tier 1 (Excellent)": {"min_score": 750, "apr": "6.49%"},
        "Tier 2 (Good)": {"min_score": 700, "apr": "8.99%"},
        "Tier 3 (Standard)": {"min_score": 650, "apr": "11.75%"}
    }

    def evaluate(self, state: ConversationState) -> Tuple[str, str, Dict[str, Any]]:
        """
        Evaluates state to determine qualification status.
        Returns (status, reason, metadata).
        Statuses:
          - qualified
          - preliminary_qualified
          - exception_review
          - disqualified
          - incomplete
        """
        # Check required fields
        if state.monthly_income is None or state.credit_score is None:
            return "incomplete", "Missing income or credit score details.", {}

        # 1. Income check
        if state.monthly_income < self.MIN_INCOME:
            return (
                "disqualified",
                f"Monthly net income of ${state.monthly_income:,.2f} is below the minimum required threshold of ${self.MIN_INCOME:,.2f}.",
                {"reason_code": "INSUFFICIENT_INCOME"}
            )

        # 2. Credit score check
        score = state.credit_score

        # Check Standard Tiers
        for tier_name, tier_info in self.TIER_RATES.items():
            if score >= tier_info["min_score"]:
                return (
                    "qualified",
                    f"Eligible for {tier_name} with fixed APR of {tier_info['apr']} and $0 prepayment penalty.",
                    {"tier": tier_name, "apr": tier_info["apr"], "prepayment_fee": "$0"}
                )

        # Near-Prime Exception check (Score 620 - 649)
        if score >= self.EXCEPTION_MIN_SCORE:
            return (
                "exception_review",
                f"Credit score of {score} is eligible under the Near-Prime Exception policy subject to a 20% down payment.",
                {"tier": "Near-Prime Exception", "requires_down_payment": True}
            )

        # Disqualified
        return (
            "disqualified",
            f"Credit score of {score} is below the minimum qualifying underwriting score of {self.MIN_CREDIT_SCORE}.",
            {"reason_code": "CREDIT_SCORE_BELOW_MINIMUM"}
        )
