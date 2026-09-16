from __future__ import annotations

import re
import unicodedata

INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_component(value: str, max_length: int = 48) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = INVALID.sub("_", value)
    value = re.sub(r"\s+", "_", value).strip(" ._")
    value = re.sub(r"_+", "_", value) or "Unknown"
    if value.upper() in RESERVED:
        value = f"_{value}"
    return value[:max_length].rstrip(" ._") or "Unknown"


def output_stem(name: str, document_type: str, language: str, company: str = "", preview: bool = False) -> str:
    person = safe_component(name, 42)
    label = "CV" if document_type == "cv" else "Anschreiben"
    parts = [person, label, safe_component(language.upper(), 8)]
    if company and company.upper() != "NEEDS_CONFIRMATION":
        parts.append(safe_component(company, 38))
    if preview:
        parts.append("DRAFT")
    return "_".join(parts)

