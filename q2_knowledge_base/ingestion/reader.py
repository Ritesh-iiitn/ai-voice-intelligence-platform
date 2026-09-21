"""
Multi-format document ingestion reader supporting PDF, TXT, HTML, CSV, and DOCX.
Includes robust extraction failure handling and metadata extraction.
"""
import os
import csv
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from pypdf import PdfReader
from bs4 import BeautifulSoup

from q2_knowledge_base.schemas.record import DocumentRecord

logger = logging.getLogger(__name__)

class DocumentIngestor:
    """Ingests multi-format source documents into standardized DocumentRecord objects."""

    def __init__(self):
        pass

    def ingest_file(self, file_path: str, default_version: str = "1.0") -> DocumentRecord:
        """Ingest a single document file from disk."""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return DocumentRecord(
                document_id=path.stem,
                title=path.name,
                source=str(path),
                source_type=path.suffix.lstrip(".").lower() or "unknown",
                content="",
                status="failed",
                error_message=f"File not found: {file_path}"
            )

        suffix = path.suffix.lower()
        source_type = suffix.lstrip(".")

        try:
            if suffix == ".pdf":
                record = self._parse_pdf(path, default_version)
            elif suffix == ".html" or suffix == ".htm":
                record = self._parse_html(path, default_version)
            elif suffix == ".csv":
                record = self._parse_csv(path, default_version)
            elif suffix == ".docx":
                record = self._parse_docx(path, default_version)
            elif suffix in [".txt", ".md"]:
                record = self._parse_text(path, default_version)
            else:
                return DocumentRecord(
                    document_id=path.stem,
                    title=path.name,
                    source=str(path),
                    source_type=source_type,
                    content="",
                    status="failed",
                    error_message=f"Unsupported file format: {suffix}"
                )

            # Check if extracted content is empty or blank
            if not record.content or not record.content.strip():
                logger.warning(f"Extracted content is empty for {file_path}")
                record.status = "empty"
                record.error_message = "Document is empty and contains no extractable text"

            return record

        except Exception as e:
            logger.exception(f"Extraction failed for {file_path}: {e}")
            return DocumentRecord(
                document_id=path.stem,
                title=path.name,
                source=str(path),
                source_type=source_type,
                content="",
                status="failed",
                error_message=f"Extraction exception: {str(e)}"
            )

    def _parse_text(self, path: Path, default_version: str) -> DocumentRecord:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        title, version, eff_date = self._extract_header_metadata(content, path.stem, default_version)
        return DocumentRecord(
            document_id=path.stem,
            title=title,
            source=str(path),
            source_type="txt",
            version=version,
            effective_date=eff_date,
            content=content,
            status="success"
        )

    def _parse_pdf(self, path: Path, default_version: str) -> DocumentRecord:
        reader = PdfReader(str(path))
        extracted_pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                extracted_pages.append(text.strip())

        content = "\n\n".join(extracted_pages)
        title, version, eff_date = self._extract_header_metadata(content, path.stem, default_version)

        return DocumentRecord(
            document_id=path.stem,
            title=title,
            source=str(path),
            source_type="pdf",
            version=version,
            effective_date=eff_date,
            content=content,
            metadata={"num_pages": len(reader.pages)},
            status="success"
        )

    def _parse_html(self, path: Path, default_version: str) -> DocumentRecord:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw_html = f.read()

        soup = BeautifulSoup(raw_html, "html.parser")

        # Extract title
        title_tag = soup.find("title") or soup.find("h1")
        title = title_tag.get_text().strip() if title_tag else path.stem

        # Extract version/metadata if present in attributes
        article = soup.find("article")
        version = default_version
        eff_date = None
        if article:
            version = article.get("data-version", default_version)
            eff_date = article.get("data-effective", None)

        # Remove header, footer, nav, script, style, cookie banners
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        for banner in soup.find_all(class_=re.compile(r"cookie|banner|nav|footer", re.I)):
            banner.decompose()

        # Format tables cleanly into Markdown / text representations
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
                if cells:
                    rows.append(" | ".join(cells))
            table_text = "\n" + "\n".join(rows) + "\n"
            table.replace_with(table_text)

        body_content = soup.get_text(separator="\n")
        # Collapse multiple newlines
        cleaned_content = re.sub(r"\n{3,}", "\n\n", body_content).strip()

        return DocumentRecord(
            document_id=path.stem,
            title=title,
            source=str(path),
            source_type="html",
            version=version,
            effective_date=eff_date,
            content=cleaned_content,
            status="success"
        )

    def _parse_csv(self, path: Path, default_version: str) -> DocumentRecord:
        rows_text = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for i, row in enumerate(reader, start=1):
                row_str = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
                rows_text.append(f"[Record {i}] {row_str}")

        content = "\n".join(rows_text)
        return DocumentRecord(
            document_id=path.stem,
            title=path.name,
            source=str(path),
            source_type="csv",
            version=default_version,
            content=content,
            metadata={"num_records": len(rows_text), "headers": headers},
            status="success"
        )

    def _parse_docx(self, path: Path, default_version: str) -> DocumentRecord:
        try:
            import docx
            doc = docx.Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n\n".join(paragraphs)
            title = paragraphs[0][:100] if paragraphs else path.stem
            return DocumentRecord(
                document_id=path.stem,
                title=title,
                source=str(path),
                source_type="docx",
                version=default_version,
                content=content,
                status="success"
            )
        except Exception as e:
            return DocumentRecord(
                document_id=path.stem,
                title=path.name,
                source=str(path),
                source_type="docx",
                content="",
                status="failed",
                error_message=f"DOCX parse failed: {e}"
            )

    def _extract_header_metadata(self, text: str, default_title: str, default_version: str):
        title = default_title
        version = default_version
        eff_date = None

        lines = text.splitlines()[:15]
        found_title = False
        for line in lines:
            clean_line = line.strip("= -#*")
            if not clean_line:
                continue
            if not found_title and ("policy" in clean_line.lower() or "guidelines" in clean_line.lower() or "rider" in clean_line.lower()):
                if "classification" not in clean_line.lower() and len(clean_line) > 5:
                    title = clean_line
                    found_title = True
            ver_match = re.search(r"version[:\s]+([0-9\.]+)", line, re.I)
            if ver_match:
                version = ver_match.group(1)
            date_match = re.search(r"effective(?:\s+date)?[:\s]+(\d{4}-\d{2}-\d{2})", line, re.I)
            if date_match:
                eff_date = date_match.group(1)

        return title, version, eff_date

    def ingest_directory(self, dir_path: str) -> List[DocumentRecord]:
        """Ingests all recognized files within a target directory."""
        records = []
        path = Path(dir_path)
        if not path.is_dir():
            logger.error(f"Directory not found: {dir_path}")
            return records

        for file_path in sorted(path.glob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                rec = self.ingest_file(str(file_path))
                records.append(rec)

        return records
