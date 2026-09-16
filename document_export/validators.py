from __future__ import annotations

import json
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from .models import StructuredDocument, ValidationResult
from .pdf_renderer import PDF_MAX_BYTES, PDF_MIN_BYTES

BLOCK_MARKERS = ("NOT_SUPPORTED", "DO_NOT_USE", "CONFLICTING")
FORBIDDEN_FIELDS = ("passport", "passport number", "reisepass", "aufenthaltstitelnummer", "marital status", "familienstand")


def read_status(application: Path) -> str:
    status_file = application / "status.md"
    if status_file.exists():
        match = re.search(r"(?:^|\n)\s*[-*]?\s*(?:status|application_status)\s*:\s*`?([a-z_]+)", status_file.read_text(encoding="utf-8-sig"), re.I)
        if match:
            return match.group(1).lower()
    metadata = application / "job-metadata.json"
    candidates = [metadata] if metadata.exists() else list(application.parent.glob(f"{application.name}.json"))
    for path in candidates:
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig")).get("application_status")
            if value:
                return str(value).lower()
        except (OSError, ValueError):
            pass
    return "draft"


def validate_export(application: Path, documents: list[StructuredDocument], mode: str, project_root: Path, force_closed: bool = False) -> ValidationResult:
    result = ValidationResult(True)
    status = read_status(application)
    result.checks.append(f"application status: {status}")
    if mode == "final":
        allowed = {"approved", "applied"}
        if force_closed:
            allowed |= {"rejected", "withdrawn"}
        if status not in allowed:
            result.blockers.append(f"final export requires approved/applied status; current status is {status}")
        required = [application / "fact-check.md", application / "source-traceability.md"]
        for path in required:
            if not path.exists():
                result.blockers.append(f"required final-export check file missing: {path.name}")
                continue
            text = path.read_text(encoding="utf-8-sig")
            for marker in BLOCK_MARKERS:
                if marker in text:
                    result.blockers.append(f"{path.name} contains blocking marker {marker}")
            if re.search(r"\b(?:critical|关键).{0,40}NEEDS_CONFIRMATION|NEEDS_CONFIRMATION.{0,40}(?:critical|关键)", text, re.I):
                result.blockers.append(f"{path.name} contains a critical NEEDS_CONFIRMATION")
        for relative in ("candidate/profile/do-not-claim.md", "candidate/profile/profile-conflicts.md"):
            path = project_root / relative
            if not path.exists():
                result.blockers.append(f"project safety file missing: {relative}")
            elif relative.endswith("profile-conflicts.md") and re.search(r"\bCONFLICTING\b", path.read_text(encoding="utf-8-sig")):
                result.blockers.append("profile-conflicts.md contains unresolved CONFLICTING status")
    combined = "\n".join(doc.plain_text() for doc in documents).casefold()
    for field in FORBIDDEN_FIELDS:
        if field in combined:
            result.blockers.append(f"document contains forbidden field: {field}")
    result.passed = not result.blockers
    return result


def validate_html(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors = []
    if "@page" not in text or "size: A4" not in text:
        errors.append("A4 print CSS missing")
    if re.search(r'(?:src|href)=["\']https?://', text, re.I):
        errors.append("external resource reference found")
    return errors


def validate_docx(path: Path) -> list[str]:
    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            required = {"[Content_Types].xml", "word/document.xml", "word/styles.xml"}
            return [] if required <= names else ["DOCX package is missing required OOXML parts"]
    except (BadZipFile, OSError) as exc:
        return [f"DOCX cannot be opened as OOXML: {exc}"]


def _font_is_embedded(font) -> bool:
    font = font.get_object()
    candidates = [font]
    descendants = font.get("/DescendantFonts") or []
    candidates.extend(item.get_object() for item in descendants)
    for candidate in candidates:
        descriptor = candidate.get("/FontDescriptor")
        if descriptor:
            descriptor = descriptor.get_object()
            if any(descriptor.get(key) for key in ("/FontFile", "/FontFile2", "/FontFile3")):
                return True
    return False


def validate_pdf(
    path: Path,
    expected_name: str = "",
    expected_experience: str = "",
    final: bool = False,
    expected_pages: int | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    untested: list[str] = []
    if not path.exists():
        return ["PDF missing"], untested
    size = path.stat().st_size
    if not PDF_MIN_BYTES <= size <= PDF_MAX_BYTES:
        errors.append(f"PDF size {size} bytes is outside the required {PDF_MIN_BYTES}-{PDF_MAX_BYTES} byte range")
    try:
        from pypdf import PdfReader
        from pypdf.generic import ContentStream
    except ImportError:
        untested.append("PDF text/page/ATS extraction not tested: pypdf is not installed in the active Python environment")
        return errors, untested
    try:
        reader = PdfReader(path)
        if expected_pages is not None and len(reader.pages) != expected_pages:
            errors.append(f"expected exactly {expected_pages} PDF pages; found {len(reader.pages)}")
        elif not 1 <= len(reader.pages) <= 5:
            errors.append(f"unexpected PDF page count: {len(reader.pages)}")
        embedded_fonts = 0
        unembedded_fonts = []
        for page_number, page in enumerate(reader.pages, start=1):
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            if abs(width - 595.28) > 1 or abs(height - 841.89) > 1:
                errors.append(f"PDF page {page_number} is not A4 portrait: {width:.2f} x {height:.2f} pt")
            resources = page.get("/Resources") or {}
            fonts = resources.get("/Font") or {}
            used_font_keys = set()
            active_font = None
            contents = page.get_contents()
            if contents is not None:
                for operands, operator in ContentStream(contents, reader).operations:
                    if operator == b"Tf" and operands:
                        active_font = str(operands[0])
                    elif operator in {b"Tj", b"TJ", b"'", b'"'} and active_font:
                        used_font_keys.add(active_font)
            for key, font in fonts.items():
                if str(key) not in used_font_keys:
                    continue
                if _font_is_embedded(font):
                    embedded_fonts += 1
                else:
                    unembedded_fonts.append(f"page {page_number} {key}")
        if not embedded_fonts:
            errors.append("PDF contains no embedded fonts")
        if unembedded_fonts:
            errors.append("PDF contains unembedded fonts: " + ", ".join(unembedded_fonts))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if len(text.strip()) < 100:
            errors.append("too little extractable PDF text")
        if expected_name and expected_name not in text:
            errors.append("candidate name not extractable from PDF")
        if expected_experience and expected_experience not in text:
            errors.append("expected experience heading not extractable from PDF")
        if final and re.search(r"\b(?:ENTWURF|DRAFT|PREVIEW|TEST WATERMARK)\b", text, re.I):
            errors.append("draft/preview/test watermark marker remains in final PDF")
        if re.search(r"(?:^|\s)#{1,6}\s|\*\*|\[[^]]+\]\([^)]+\)", text):
            errors.append("Markdown markers remain in PDF text")
        if "Deutsch" in text and not any(ch in text for ch in "äöüÄÖÜß"):
            untested.append("German special-character integrity could not be positively established")
    except Exception as exc:
        errors.append(f"PDF validation failed: {exc}")
    return errors, untested
