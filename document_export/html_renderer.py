from __future__ import annotations

from html import escape
from pathlib import Path
import re

from .models import Block, InlineRun, StructuredDocument
from .template_config import resolve_template


SECTION_LABELS = {
    "Ausgewählte Projekte und Ergebnisse": "Projekte",
    "Relevante Kompetenzen": "Kompetenzen",
}


def _runs(runs: tuple[InlineRun, ...]) -> str:
    out = []
    for run in runs:
        value = escape(run.text)
        if run.bold:
            value = f"<strong>{value}</strong>"
        if run.italic:
            value = f"<em>{value}</em>"
        out.append(value)
    return "".join(out)


def _bold_only(block: Block) -> bool:
    meaningful = [run for run in block.runs if run.text.strip()]
    return bool(meaningful) and all(run.bold for run in meaningful)


def _contact_line(value: str) -> str:
    return re.sub(r"\s*[·|]\s*", " | ", value.strip())


def _entry_parts(value: str) -> tuple[str, str]:
    left, separator, right = value.partition(" · ")
    return (left.strip(), right.strip()) if separator else (value.strip(), "")


def render_html(doc: StructuredDocument, template_root: Path, preview: bool = False, template_id: str = "") -> str:
    css = (template_root / "shared" / "base.css").read_text(encoding="utf-8")
    template_name = "resume" if doc.document_type == "cv" else "cover-letter"
    selection = resolve_template(template_root, doc.document_type, doc.language, template_id)
    css += "\n" + (selection.path / f"{template_name}.css").read_text(encoding="utf-8")
    template = (selection.path / f"{template_name}.html.j2").read_text(encoding="utf-8")
    body: list[str] = []
    list_open = False
    section_open = False
    current_section = ""
    title_seen = False
    index = 0
    while index < len(doc.blocks):
        block = doc.blocks[index]
        if block.kind != "bullet" and list_open:
            body.append("</ul>")
            list_open = False
        content = _runs(block.runs)
        if block.kind == "heading":
            level = min(max(block.level, 1), 4)
            if doc.document_type == "cv" and level == 1 and not title_seen:
                body.append(f'<h1 class="candidate-name">{content}</h1>')
                title_seen = True
            elif doc.document_type == "cv" and level == 2:
                if section_open:
                    body.append("</section>")
                    section_open = False
                current_section = SECTION_LABELS.get(block.text, block.text)
                if current_section == "Kompetenzen":
                    body.append('<section class="competencies-section">')
                    section_open = True
                body.append(f'<h2 class="section-heading">{escape(current_section)}</h2>')
            elif (
                doc.document_type == "cv"
                and level == 3
                and current_section in {"Berufserfahrung", "Ausbildung"}
                and index + 1 < len(doc.blocks)
                and doc.blocks[index + 1].kind == "paragraph"
                and _bold_only(doc.blocks[index + 1])
            ):
                primary, secondary = _entry_parts(block.text)
                date = doc.blocks[index + 1].text
                entry_class = "job-entry" if current_section == "Berufserfahrung" else "education-entry"
                body.extend([
                    f'<div class="entry-header {entry_class}">',
                    f'<h3 class="entry-title"><span class="entry-role">{escape(primary)}</span>'
                    + (f'<span class="entry-organization"> · {escape(secondary)}</span>' if secondary else "")
                    + "</h3>",
                    f'<p class="entry-date">{escape(date)}</p>',
                    "</div>",
                ])
                index += 1
            else:
                body.append(f"<h{level}>{content}</h{level}>")
        elif block.kind == "bullet":
            if not list_open:
                body.append("<ul>")
                list_open = True
            body.append(f"<li>{content}</li>")
        elif block.kind == "quote":
            body.append(f"<aside>{content}</aside>")
        elif doc.document_type == "cv" and title_seen and block.text == doc.contact_line:
            body.append(f'<p class="contact-line">{escape(_contact_line(block.text))}</p>')
        elif (
            doc.document_type == "cv"
            and current_section == "Kompetenzen"
            and _bold_only(block)
            and index + 1 < len(doc.blocks)
            and doc.blocks[index + 1].kind == "paragraph"
        ):
            body.extend([
                '<div class="skill-group">',
                f'<h3 class="skill-group-title">{content}</h3>',
                f'<p class="skill-group-values">{_runs(doc.blocks[index + 1].runs)}</p>',
                "</div>",
            ])
            index += 1
        else:
            body.append(f"<p>{content}</p>")
        index += 1
    if list_open:
        body.append("</ul>")
    if section_open:
        body.append("</section>")
    watermark = '<div class="draft-watermark" aria-label="Preview">DRAFT</div>' if preview else ""
    label = "Lebenslauf" if doc.document_type == "cv" else "Anschreiben"
    document_body = template.replace("{{ content }}", "\n".join(part for part in body if part))
    return "<!doctype html>\n<html lang=\"{}\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>{}</title><style>{}</style></head><body>{}{}</body></html>\n".format(escape(doc.language), escape(f"{doc.title} – {label}"), css, watermark, document_body)
