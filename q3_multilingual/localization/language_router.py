"""
Language detection and routing module ensuring calls maintain regional registers.
"""
import re
from typing import Tuple

class LanguageRouter:
    """Routes customer utterances to localized voice bots and prevents unexpected fallback to English."""

    TAGALOG_MARKERS = [
        r"\b(?:po|opo|magandang|araw|salamat|oo|hindi|gusto|uutangin|sweldo|kita|kotse|piso|pera|kayo|ninyo|ba|nga|eh)\b"
    ]

    INDONESIA_MARKERS = [
        r"\b(?:halo|selamat|siang|pagi|bapak|ibu|terima|kasih|ya|tidak|nggak|bisa|cicilan|tenor|denda|angsuran|pembiayaan|bunga|rupiah|juta|mas|nyuwun|sewu|nek|piro)\b"
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
