"""
Localized Tagalog and Taglish dialog prompts for the Philippines voice agent.
"""

PH_PROMPTS = {
    "greeting": (
        "Magandang araw po! Alex po ito mula sa Apex Lending and Credit Protection. "
        "Follow up lang po ako regarding sa inyong vehicle financing at loan protection inquiry. "
        "Kausap ko po ba si {name}?"
    ),
    "consent_request": (
        "Salamat po! Bago po tayo magpatuloy para sa inyong pre-approval options, "
        "inform ko lang po kayo na recorded po ang call na ito for quality and compliance. "
        "Okay lang po ba sa inyo na magpatuloy tayo?"
    ),
    "consent_declined": (
        "Naiintindihan ko po. Dahil requirement po sa compliance ang recording para sa phone quotation, "
        "hindi po tayo makakapag-proceed over the phone. Pwede po namin kayong padalhan ng secure application link sa inyong email or SMS. Okay po ba iyon?"
    ),
    "ask_amount": (
        "Sige po. Para po makapili tayo ng pinakamagandang rate at payment terms, "
        "magkano po ang target ninyong halaga na hihiramin o i-finance?"
    ),
    "ask_income": (
        "Noted po. At para po masigurado natin ang debt-to-income approval, "
        "magkano po humigit-kumulang ang inyong buwanang net take-home pay o sweldo?"
    ),
    "ask_credit_score": (
        "Salamat po. Panghuli po, may idea po ba kayo sa inyong approximate credit score range or credit standing?"
    ),
    "objection_rate_high": (
        "Naiintindihan ko po kayo nang mabuti. Ang kagandahan po sa offer natin, fixed po ang interest rate mula 6.49% "
        "at mayroon po tayong zero prepayment penalty. Kaya pwede niyo pong bayaran nang mas maaga ang principal para mas makatipid sa interest. "
        "Gusto niyo po bang i-check natin ang estimated monthly computation ninyo?"
    ),
    "insurance_rider_info": (
        "Kasama po sa ating proteksyon ang Involuntary Unemployment Rider na sumasagot ng hanggang 6 months na hulog "
        "kung sakaling magkaroon ng company redundancy, at may Credit Life Insurance din po para sa inyong designated beneficiary."
    ),
    "unsupported_fallback": (
        "Pasensya na po, wala po akong maaasahang impormasyon tungkol diyan sa aming available policy guidelines. "
        "Mas mainam po na i-connect ko kayo sa aming senior lending specialist para masagot po ito nang kumpleto."
    ),
    "escalation_transfer": (
        "Walang problema po. Ititigil ko po ang automated assessment at ita-transfer ko po kayo agad "
        "sa isa sa aming licensed specialist. Paki-hold lang po ang inyong linya sandali."
    ),
    "wrapup_qualified": (
        "Magandang balita po! Preliminarily qualified po kayo para sa {tier_name} na may fixed APR na {apr} "
        "at zero prepayment penalty. Na-generate na po ang inyong reference lead number: {lead_id}."
    ),
    "wrapup_disqualified": (
        "Salamat po sa inyong oras. Sa ngayon po, hindi pa po umabot ang inyong detalye sa minimum criteria na "
        "₱140,000 buwanang kita o 650 credit score. Magpapadala po kami ng credit enhancement guide sa inyong email."
    )
}
