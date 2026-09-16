from __future__ import annotations

import re
from pathlib import Path

from .models import Block, InlineRun, StructuredDocument

DRAFT_RE = re.compile(r"\b(ENTWURF|DRAFT|zur persönlichen Prüfung|nicht versendet)\b", re.I)
INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")


def parse_inline(text: str) -> tuple[InlineRun, ...]:
    runs: list[InlineRun] = []
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            runs.append(InlineRun(part[2:-2], bold=True))
        elif part.startswith("*") and part.endswith("*"):
            runs.append(InlineRun(part[1:-1], italic=True))
        else:
            runs.append(InlineRun(part))
    return tuple(runs)


def parse_markdown(path: Path, document_type: str = "auto", language: str = "de") -> StructuredDocument:
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if document_type == "auto":
        document_type = "cover-letter" if "cover-letter" in path.name.lower() or "anschreiben" in path.name.lower() else "cv"
    doc = StructuredDocument(path, document_type, language)
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            value = " ".join(item.strip() for item in paragraph).strip()
            if value:
                doc.blocks.append(Block("paragraph", runs=parse_inline(value)))
            paragraph.clear()

    for raw in text.splitlines():
        line = raw
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith(">"):
            flush()
            quote = stripped.lstrip("> ").strip()
            if DRAFT_RE.search(re.sub(r"[*_`]", "", quote)):
                doc.draft_markers_removed += 1
                continue
            doc.blocks.append(Block("quote", runs=parse_inline(quote)))
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush()
            level = len(heading.group(1))
            value = heading.group(2).strip()
            block = Block("heading", level=level, runs=parse_inline(value))
            doc.blocks.append(block)
            if level == 1 and not doc.title:
                doc.title = block.text
            continue
        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        if bullet:
            flush()
            doc.blocks.append(Block("bullet", runs=parse_inline(bullet.group(1))))
            continue
        if not doc.contact_line and doc.title and len(doc.blocks) == 1:
            doc.contact_line = re.sub(r"[*_`]", "", stripped)
        paragraph.append(stripped.rstrip("  "))
        if line.endswith("  "):
            flush()
    flush()
    return doc
