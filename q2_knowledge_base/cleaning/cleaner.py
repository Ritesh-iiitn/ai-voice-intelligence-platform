"""
Content cleaning module to remove boilerplate, navigation artifacts, repeated paragraphs,
and marketing noise while preserving structural headings, policy clauses, and tables.
"""
import re
from typing import List, Set

class DocumentCleaner:
    """Cleans document text content without destroying policy context or tables."""

    # Common noise patterns
    BOILERPLATE_PATTERNS = [
        r"we use cookies.*?accept.*?(?:\n|$)",
        r"cookie policy.*?(?:\n|$)",
        r"all rights reserved.*?(?:\n|$)",
        r"navigation links:.*?(?:\n|$)",
        r"click here to (?:subscribe|read more|contact).*?(?:\n|$)",
        r"follow us on (?:twitter|facebook|linkedin|instagram).*?(?:\n|$)",
        r"privacy policy\s*\|\s*terms of service",
    ]

    def __init__(self):
        self.compiled_noise = [re.compile(p, re.I) for p in self.BOILERPLATE_PATTERNS]

    def clean_text(self, text: str) -> str:
        """Clean raw text while preserving tables, headings, and lists."""
        if not text:
            return ""

        # Step 1: Remove noisy boilerplate lines
        cleaned = text
        for pattern in self.compiled_noise:
            cleaned = pattern.sub("", cleaned)

        # Step 2: Normalize unicode whitespace & characters
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = cleaned.replace("\u2013", "-").replace("\u2014", "--")
        cleaned = cleaned.replace("\u2018", "'").replace("\u2019", "'")
        cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"')

        # Step 3: Deduplicate identical consecutive paragraphs/lines while preserving table rows
        lines = cleaned.split("\n")
        deduped_lines: List[str] = []
        last_line = ""

        for line in lines:
            stripped = line.strip()
            # If line is identical to previous non-empty line and isn't a table divider or bullet
            if stripped and stripped == last_line and not stripped.startswith("|") and not stripped.startswith("-"):
                continue
            deduped_lines.append(line)
            if stripped:
                last_line = stripped

        # Step 4: Normalize excessive blank lines (more than 2 consecutive blank lines)
        result = "\n".join(deduped_lines)
        result = re.sub(r"\n{3,}", "\n\n", result)

        return result.strip()
