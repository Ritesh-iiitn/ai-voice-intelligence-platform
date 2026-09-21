"""
Indonesian financial terminology, Rupiah currency parser, regional accent fixtures,
and documented ASR observation notes.
"""
import re
from typing import Dict, Optional, List, Any

# Core consumer credit terminology
ID_FINANCIAL_TERMINOLOGY: Dict[str, str] = {
    "cicilan": "pembayaran berkala per bulan (monthly installment)",
    "tenor": "jangka waktu pinjaman atau pembiayaan (loan duration/tenor)",
    "denda": "biaya keterlambatan pembayaran (late penalty fee)",
    "dp": "uang muka pembayaran (down payment)",
    "jatuh tempo": "tanggal batas akhir pembayaran (due date)",
    "angsuran": "jumlah setoran bulanan (installment amount)",
    "pembiayaan": "fasilitas kredit atau pinjaman kendaraan (financing)",
    "bunga": "suku bunga tahunan (APR)",
    "pelunasan dipercepat": "pembayaran sisa pokok lebih awal tanpa denda (prepayment)"
}

# Regional Accent and Dialect Fixtures
REGIONAL_DIALECT_FIXTURES = [
    {
        "dialect": "Javanese-influenced Colloquial Indonesian (Central/East Java)",
        "input_phrase": "Nyuwun sewu mas, nek cicilan per bulane piro yo nek jupuk tenor 24 wulan? Kena denda telat gak?",
        "standard_bahasa_equivalent": "Permisi mas, berapa cicilan per bulannya jika mengambil tenor 24 bulan? Apakah dikenakan denda keterlambatan?",
        "asr_challenge": "Javanese lexical insertions ('nyuwun sewu', 'nek', 'piro', 'wulan') often confuse standard acoustic language models configured strictly for formal Indonesian.",
        "routing_action": "Extract core terms: 'cicilan', 'tenor 24', 'denda'. Maintain polite regional acknowledgment without falling back to English."
    },
    {
        "dialect": "Colloquial Jakarta Slang (Bahasa Gaul)",
        "input_phrase": "Bisa kurang gak bunganya? Terus kalo mau lunasin cepet ada denda penaltinya gak sih?",
        "standard_bahasa_equivalent": "Apakah suku bunganya dapat dikurangi? Kemudian jika ingin melunasi lebih cepat apakah dikenakan denda penalti?",
        "asr_challenge": "Particle elisions ('gak', 'sih', 'lunasin cepet') deviate from standard dictionary lemmas ('tidak', 'melunasi lebih cepat').",
        "routing_action": "Recognize 'lunasin cepet' as 'pelunasan dipercepat' ($0 prepayment penalty)."
    }
]

# Actual ASR Observations
ASR_OBSERVATIONS_ID = {
    "provider_tested": "Whisper-Large-v3 / Deepgram Nova-2 (id)",
    "loanword_fidelity": "High accuracy on standard financial terms ('tenor', 'down payment', 'APR'), but tendency to mis-segment Indonesian compound phrases like 'jatuh tempo' as 'jatuhtempo'.",
    "colloquial_particles": "Words like 'nggak', 'banget', 'dong', 'kan' are transcribed accurately, but morphological prefixes ('di-', 'me-') in informal speech are frequently dropped or transcribed phonetically.",
    "regional_accent_dropoff": "Substantial Word Error Rate (WER) degradation (estimated 22-28% WER increase) when Javanese or Sundanese intonation and regional vocabulary are introduced without custom acoustic adaptation.",
    "mitigation_strategy": "Prepend phonetic and synonym expansion dictionary in normalizer; never switch language register to English on unrecognized colloquial tokens."
}

def parse_idr_amount(text: str) -> Optional[float]:
    """Parse Indonesian Rupiah amounts from text (e.g. 'Rp 150.000.000', '150 juta', '25jt')."""
    clean = text.lower().replace(".", "").replace(",", "")
    
    # Check 'juta' or 'jt' (million)
    juta_match = re.search(r"(?:rp)?\s*(\d+(?:\.\d+)?)\s*(?:juta|jt)\b", clean)
    if juta_match:
        return float(juta_match.group(1)) * 1_000_000.0

    # Check 'ribu' or 'rb' (thousand)
    ribu_match = re.search(r"(?:rp)?\s*(\d+(?:\.\d+)?)\s*(?:ribu|rb)\b", clean)
    if ribu_match:
        return float(ribu_match.group(1)) * 1_000.0

    # Check direct numbers
    num_match = re.search(r"(?:rp)?\s*(\d{6,12})\b", clean)
    if num_match:
        return float(num_match.group(1))

    return None

def format_idr_currency(amount: float) -> str:
    """Format float into Rupiah string representation."""
    return f"Rp {amount:,.0f}".replace(",", ".")
