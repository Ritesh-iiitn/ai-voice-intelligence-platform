"""
Philippine financial and insurance terminology dictionaries and currency formatters.
Covers English, Tagalog, and natural Taglish expressions.
"""
import re
from typing import Dict, Optional

# Core financial and life-insurance domain terms
PH_FINANCIAL_TERMINOLOGY: Dict[str, str] = {
    # Insurance Concepts
    "premium": "buwanang hulog sa proteksyon (premium)",
    "policy": "polisya o kontrata ng seguro (policy)",
    "beneficiary": "itinalagang benepisyaryo (beneficiary)",
    "rider": "karagdagang proteksyon o coverage (rider)",
    "lapse": "pagkapaso o pagka-kansela ng proteksyon (policy lapse)",
    "coverage": "saklaw ng proteksyon (coverage)",
    "bank referral": "endorsement sa ka-partner na bangko (bank referral)",
    
    # Loan & Credit Concepts
    "interest": "patong na interes (APR)",
    "loan amount": "halaga ng uutangin (loan amount)",
    "monthly payment": "buwanang hulog o installment",
    "prepayment": "maagang pagbayad nang buo (prepayment)",
    "down payment": "paunang bayad (DP)",
    "grace period": "palugit sa pagbabayad (grace period)"
}

# 3+ Documented Examples of Localization vs Direct Word-for-Word Translation
LOCALIZATION_EXAMPLES_PH = [
    {
        "domain_aspect": "Consent and Quality Disclosure",
        "literal_translation": "Bago tayo magpatuloy, nais kong ipaalam sa iyo na ang tawag na ito ay inirerekord para sa mga layunin ng kalidad.",
        "natural_taglish_localized": "Bago po tayo magpatuloy, inform ko lang po kayo na recorded po ang call na ito for quality and compliance. Okay lang po ba sa inyo?",
        "cultural_rationale": "Direct translation sounds robotic and archaic in Philippine banking. Filipino consumers expect polite conversational Taglish with 'po/opo' and standard industry loanwords like 'recorded', 'compliance', and 'call'."
    },
    {
        "domain_aspect": "Insurance Rider & Beneficiary Explanation",
        "literal_translation": "Ang saklaw ng kamatayan sa kredito ay magbabayad ng iyong balanse sa bangko at magbibigay ng pera sa iyong tagapagmana.",
        "natural_taglish_localized": "Napakaganda po ng ating Credit Life Rider kasi kung sakaling may mangyari sa inyo, fully paid po ang natitirang balance ng loan ninyo at may dagdag pang ₱10,000 na cash benefit na ibibigay nang direkta sa designated beneficiary ninyo para sa pamilya.",
        "cultural_rationale": "Emphasizes family peace of mind and protection of loved ones, using familiar financial terms ('fully paid', 'designated beneficiary', 'cash benefit') rather than legalistic Tagalog words."
    },
    {
        "domain_aspect": "Rate Objection & Early Payoff Flexibility",
        "literal_translation": "Naiintindihan ko na ang interes ay mataas, ngunit maaari kang magbayad nang mas maaga nang walang multa.",
        "natural_taglish_localized": "Naiintindihan ko po kayo, Sir/Ma'am. Ang maganda po sa loan natin, fixed po ang interest rate at zero prepayment penalty. Ibig sabihin, pwede niyo pong bayaran agad nang buo o mag-advance payment anytime nang walang penalty para mas mababa ang kabuuang interest.",
        "cultural_rationale": "Validates the customer's budget sensitivity empathetically and highlights concrete savings through early prepayment flexibility."
    }
]

def format_php_currency(amount: float) -> str:
    """Format numeric amount into Philippine Peso representation."""
    return f"₱{amount:,.2f}"

def parse_php_amount(text: str) -> Optional[float]:
    """Extract PHP or Peso amounts from Tagalog/Taglish text."""
    # Matches '₱500,000', 'PHP 50k', '50k', '50,000 piso'
    match = re.search(r"(?:₱|php|piso)?\s*([\d,]+(?:\.\d+)?)\s*(?:k|libo|piso)?\b", text, re.I)
    if match:
        num_str = match.group(1).replace(",", "")
        try:
            val = float(num_str)
            # Only multiply if 'k' or 'libo' is directly adjacent to number or standalone token
            if re.search(r"\d+\s*(?:k|libo)\b", text, re.I):
                val *= 1000.0
            return val
        except ValueError:
            return None
    return None
