"""
Language detection and routing module ensuring calls maintain regional registers.
"""
from __future__ import annotations

from enum import Enum
import re
from typing import NamedTuple, Optional


class SupportedMarket(str, Enum):
    PH = "PH"
    ID = "ID"
    US = "US"


class RouteDecision(NamedTuple):
    market: SupportedMarket
    confidence: float
    detected_markers: list[str]
    bot_engine_name: str


class LanguageRouter:
    """Routes customer utterances to localized voice bots and prevents unexpected fallback to English."""

    TAGALOG_MARKERS = [
        r"\b(?:po|opo|magandang|araw|salamat|oo|hindi|gusto|uutangin|sweldo|kita|kotse|piso|pera|kayo|ninyo|ba|nga|eh|magkano|premium|rider|beneficiary|lapse)\b"
    ]

    INDONESIA_MARKERS = [
        r"\b(?:halo|selamat|siang|pagi|bapak|ibu|terima|kasih|ya|tidak|nggak|bisa|cicilan|tenor|denda|angsuran|pembiayaan|bunga|rupiah|juta|mas|nyuwun|sewu|nek|piro|dp|down payment)\b"
    ]

    def detect_language(self, text: str) -> str:
        """
        Detects language of utterance: 'philippines', 'indonesia', or 'english'.
        """
        clean = text.lower()

        # Check Tagalog / Taglish
        for pat in self.TAGALOG_MARKERS:
            if re.search(pat, clean):
                return "philippines"

        # Check Bahasa Indonesia / Javanese
        for pat in self.INDONESIA_MARKERS:
            if re.search(pat, clean):
                return "indonesia"

        return "english"

    def route(self, text: str, country_code: Optional[str] = None) -> RouteDecision:
        """Rich routing decision returning market, confidence, and target bot."""
        lang = self.detect_language(text)
        detected: list[str] = []
        clean = text.lower()

        if lang == "philippines" or (country_code and country_code.upper() == "PH"):
            for pat in self.TAGALOG_MARKERS:
                matches = re.findall(pat, clean)
                detected.extend(matches)
            return RouteDecision(
                market=SupportedMarket.PH,
                confidence=0.95 if detected else 0.80,
                detected_markers=list(set(detected)),
                bot_engine_name="PhilippinesTaglishBot",
            )
        elif lang == "indonesia" or (country_code and country_code.upper() == "ID"):
            for pat in self.INDONESIA_MARKERS:
                matches = re.findall(pat, clean)
                detected.extend(matches)
            return RouteDecision(
                market=SupportedMarket.ID,
                confidence=0.95 if detected else 0.80,
                detected_markers=list(set(detected)),
                bot_engine_name="IndonesiaBahasaBot",
            )
        else:
            return RouteDecision(
                market=SupportedMarket.US,
                confidence=0.75,
                detected_markers=[],
                bot_engine_name="VoiceAgentEngine",
            )
