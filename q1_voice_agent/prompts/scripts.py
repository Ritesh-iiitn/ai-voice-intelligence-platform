"""
Standardized voice agent scripts and dialog templates.
"""

VOICE_SCRIPTS = {
    "greeting": (
        "Hello! This is Alex calling from Apex Credit & Vehicle Lending. "
        "I'm following up on your inquiry regarding our pre-approved auto and flexi-credit options. "
        "Am I speaking with {name}?"
    ),
    "consent_request": (
        "Great! Before we proceed to review your financing options, I want to inform you that "
        "this call is recorded for quality, compliance, and training purposes. Is it okay to continue?"
    ),
    "consent_declined": (
        "I completely understand. Because compliance regulations require recording for telephone quotes, "
        "I cannot proceed over the phone. I can have an advisor email your details, or would you prefer a secure web portal link?"
    ),
    "ask_purpose": (
        "Thank you! To find your best rate, what will you be using the financing for—is this for a new or used vehicle purchase, or personal credit?"
    ),
    "ask_amount": (
        "Understood. Approximately how much funding or borrowing amount are you looking to finance?"
    ),
    "ask_income": (
        "Got it. And to check your debt-to-income eligibility, what is your approximate monthly net take-home income?"
    ),
    "ask_credit_score": (
        "Thank you. Lastly, what is your approximate credit score or credit rating range?"
    ),
    "conflict_clarification": (
        "I want to make sure I have your exact details right. Earlier you mentioned {prev_val}, but just now you mentioned {new_val}. "
        "Which figure should I record for your pre-qualification?"
    ),
    "unsupported_fallback": (
        "I don't have reliable information about that in my available business policies. "
        "I would be happy to connect you with a senior lending specialist who can answer that in detail."
    ),
    "escalation_transfer": (
        "Certainly. I am stopping the automated assessment and transferring you directly to a licensed human specialist. "
        "Please stay on the line while I connect you."
    ),
    "wrapup_qualified": (
        "Fantastic news! Based on our underwriting guidelines, you are preliminarily qualified for {tier_name} "
        "with a fixed APR of {apr} with a $0 prepayment penalty. I have generated your pre-approval reference {lead_id}."
    ),
    "wrapup_exception": (
        "Thank you for sharing your details. Your profile qualifies under our Special Near-Prime Exception Program, "
        "requiring a 20% down payment. I have referred your file to our underwriting committee under reference {lead_id}."
    ),
    "wrapup_disqualified": (
        "Thank you for your time. At present, your details do not meet our minimum underwriting threshold of "
        "$2,500 monthly income or 650 credit score. We will send a complimentary credit enhancement guide to your contact information."
    )
}
