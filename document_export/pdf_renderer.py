from __future__ import annotations

import importlib.util
from html import escape
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .models import Block, StructuredDocument
from .template_config import DEFAULT_GERMAN_CV_TEMPLATE, LEGACY_RESUME_TEMPLATE


SECTION_LABELS = {
    "Ausgewählte Projekte und Ergebnisse": "Projekte",
    "Relevante Kompetenzen": "Kompetenzen",
}

PDF_MIN_BYTES = 50 * 1024
PDF_MAX_BYTES = 200 * 1024


@dataclass(frozen=True)
class PdfBackend:
    name: str
    executable: str = ""


def _browser_candidates() -> list[tuple[str, Path]]:
    env_paths = [
        ("chrome", Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")),
        ("chrome", Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")),
        ("edge", Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")),
        ("edge", Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")),
    ]
    return env_paths


def select_pdf_backend() -> PdfBackend | None:
    backends = available_pdf_backends()
    return backends[0] if backends else None


def available_pdf_backends() -> list[PdfBackend]:
    backends: list[PdfBackend] = []
    seen: set[str] = set()
    for name in ("chrome", "msedge"):
        executable = shutil.which(name) or shutil.which(f"{name}.exe")
        if executable:
            backend_name = "chrome" if name == "chrome" else "edge"
            backends.append(PdfBackend(backend_name, executable))
            seen.add(backend_name)
    for name, path in _browser_candidates():
        if path.is_file() and name not in seen:
            backends.append(PdfBackend(name, str(path)))
            seen.add(name)
    if importlib.util.find_spec("weasyprint"):
        backends.append(PdfBackend("weasyprint"))
    if importlib.util.find_spec("reportlab"):
        backends.append(PdfBackend("reportlab"))
    return backends


def _bold_only(block: Block) -> bool:
    meaningful = [run for run in block.runs if run.text.strip()]
    return bool(meaningful) and all(run.bold for run in meaningful)


def _contact_line(value: str) -> str:
    return re.sub(r"\s*[·|]\s*", " | ", value.strip())


def _entry_parts(value: str) -> tuple[str, str]:
    left, separator, right = value.partition(" · ")
    return (left.strip(), right.strip()) if separator else (value.strip(), "")


def _register_embedded_font_family() -> dict[str, str]:
    """Register a local TrueType family so application PDFs contain real fonts."""
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    reportlab_fonts = Path(reportlab.__file__).resolve().parent / "fonts"
    families = [
        (
            "Arial",
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
            Path(r"C:\Windows\Fonts\ariali.ttf"),
            Path(r"C:\Windows\Fonts\arialbi.ttf"),
        ),
        (
            "LiberationSans",
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-BoldItalic.ttf"),
        ),
        (
            "DejaVuSans",
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
        ),
        (
            "BitstreamVeraSans",
            reportlab_fonts / "Vera.ttf",
            reportlab_fonts / "VeraBd.ttf",
            reportlab_fonts / "VeraIt.ttf",
            reportlab_fonts / "VeraBI.ttf",
        ),
    ]
    for family, regular, bold, italic, bold_italic in families:
        files = (regular, bold, italic, bold_italic)
        if not all(path.is_file() for path in files):
            continue
        aliases = {
            "regular": f"AJExport-{family}-Regular",
            "bold": f"AJExport-{family}-Bold",
            "italic": f"AJExport-{family}-Italic",
            "bold_italic": f"AJExport-{family}-BoldItalic",
        }
        for alias, path in zip(aliases.values(), files):
            if alias not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(alias, str(path)))
        pdfmetrics.registerFontFamily(
            aliases["regular"],
            normal=aliases["regular"],
            bold=aliases["bold"],
            italic=aliases["italic"],
            boldItalic=aliases["bold_italic"],
        )
        return aliases
    raise RuntimeError("No complete local TrueType font family is available for embedded-font PDF export")


def _render_reportlab(doc: StructuredDocument, output: Path, preview: bool, template_id: str = "") -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Table, TableStyle

    fonts = _register_embedded_font_family()
    base = getSampleStyleSheet()
    effective_template = template_id or (DEFAULT_GERMAN_CV_TEMPLATE if doc.document_type == "cv" and doc.language == "de" else LEGACY_RESUME_TEMPLATE)
    if doc.document_type == "cv" and effective_template not in {DEFAULT_GERMAN_CV_TEMPLATE, LEGACY_RESUME_TEMPLATE}:
        raise ValueError(f"unsupported PDF resume template: {effective_template}")
    styles = {
        "body": ParagraphStyle("ExportBody", parent=base["BodyText"], fontName=fonts["regular"], fontSize=9.8, leading=13.4, textColor=colors.HexColor("#20252B"), spaceAfter=4.5),
        "contact": ParagraphStyle("ExportContact", parent=base["BodyText"], fontName=fonts["regular"], fontSize=9.2, leading=11, textColor=colors.HexColor("#5F6872"), spaceAfter=13, keepWithNext=True),
        "h1": ParagraphStyle("ExportTitle", parent=base["Title"], fontName=fonts["bold"], fontSize=22, leading=23.5, alignment=TA_LEFT, textColor=colors.HexColor("#263746"), spaceAfter=3, keepWithNext=True),
        "h2": ParagraphStyle("ExportH1", parent=base["Heading1"], fontName=fonts["bold"], fontSize=12.8, leading=14, textColor=colors.HexColor("#263746"), spaceBefore=15, spaceAfter=4, keepWithNext=True),
        "h3": ParagraphStyle("ExportH2", parent=base["Heading2"], fontName=fonts["bold"], fontSize=10.8, leading=12.5, textColor=colors.HexColor("#20252B"), spaceBefore=8, spaceAfter=3, keepWithNext=True),
        "entry_role": ParagraphStyle("EntryRole", parent=base["BodyText"], fontName=fonts["bold"], fontSize=11.2, leading=12.5, textColor=colors.HexColor("#20252B")),
        "entry_date": ParagraphStyle("EntryDate", parent=base["BodyText"], fontName=fonts["bold"], fontSize=9.3, leading=11, alignment=TA_RIGHT, textColor=colors.HexColor("#5F6872")),
        "entry_org": ParagraphStyle("EntryOrganization", parent=base["BodyText"], fontName=fonts["bold"], fontSize=9.7, leading=11.5, textColor=colors.HexColor("#5F6872")),
        "skill_title": ParagraphStyle("SkillGroupTitle", parent=base["BodyText"], fontName=fonts["bold"], fontSize=9.8, leading=11.5, textColor=colors.HexColor("#20252B"), spaceAfter=1.5, keepWithNext=True),
        "skill_values": ParagraphStyle("SkillGroupValues", parent=base["BodyText"], fontName=fonts["regular"], fontSize=9.5, leading=12.7, textColor=colors.HexColor("#343B43"), spaceAfter=5),
        "quote": ParagraphStyle("ExportQuote", parent=base["BodyText"], fontName=fonts["italic"], fontSize=9.3, leading=12, leftIndent=12, textColor=colors.HexColor("#5F6872"), spaceAfter=6),
        "bullet": ParagraphStyle("ExportBullet", parent=base["BodyText"], fontName=fonts["regular"], fontSize=9.7, leading=12.8, textColor=colors.HexColor("#20252B"), leftIndent=14, firstLineIndent=-8, spaceAfter=2.7),
    }

    def rich(block) -> str:
        parts = []
        for run in block.runs:
            value = escape(run.text)
            if run.bold:
                value = f"<b>{value}</b>"
            if run.italic:
                value = f"<i>{value}</i>"
            parts.append(value)
        return "".join(parts)

    story = []
    current_section = ""
    title_seen = False
    usable_width = A4[0] - 40 * mm
    index = 0
    while index < len(doc.blocks):
        block = doc.blocks[index]
        if block.kind == "bullet":
            story.append(Paragraph("- " + rich(block), styles["bullet"]))
            index += 1
            continue
        if block.kind == "heading":
            if doc.document_type == "cv" and block.level == 1 and not title_seen:
                story.append(Paragraph(rich(block), styles["h1"]))
                title_seen = True
            elif doc.document_type == "cv" and block.level == 2:
                current_section = SECTION_LABELS.get(block.text, block.text)
                rule = HRFlowable(width="100%", thickness=0.45, color=colors.HexColor("#D6DADE"), spaceBefore=0, spaceAfter=6)
                rule._keepWithNext = True
                heading = Paragraph(escape(current_section), styles["h2"])
                if current_section == "Kompetenzen":
                    section_story = [heading, rule]
                    next_index = index + 1
                    while next_index < len(doc.blocks):
                        section_block = doc.blocks[next_index]
                        if section_block.kind == "heading" and section_block.level == 2:
                            break
                        if (
                            section_block.kind == "paragraph"
                            and _bold_only(section_block)
                            and next_index + 1 < len(doc.blocks)
                            and doc.blocks[next_index + 1].kind == "paragraph"
                        ):
                            section_story.extend([
                                Paragraph(rich(section_block), styles["skill_title"]),
                                Paragraph(rich(doc.blocks[next_index + 1]), styles["skill_values"]),
                            ])
                            next_index += 2
                            continue
                        section_style = styles["h3"] if section_block.kind == "heading" else styles["bullet"] if section_block.kind == "bullet" else styles["body"]
                        prefix = "- " if section_block.kind == "bullet" else ""
                        section_story.append(Paragraph(prefix + rich(section_block), section_style))
                        next_index += 1
                    story.append(KeepTogether(section_story))
                    index = next_index
                    continue
                story.extend([heading, rule])
            elif (
                doc.document_type == "cv"
                and block.level == 3
                and current_section in {"Berufserfahrung", "Ausbildung"}
                and index + 1 < len(doc.blocks)
                and doc.blocks[index + 1].kind == "paragraph"
                and _bold_only(doc.blocks[index + 1])
            ):
                primary, secondary = _entry_parts(block.text)
                date = doc.blocks[index + 1].text
                left_value = f"<b>{escape(primary)}</b>"
                if secondary:
                    left_value += f'<font color="#5F6872" size="9.7"> · {escape(secondary)}</font>'
                rows = [[Paragraph(left_value, styles["entry_role"]), Paragraph(escape(date), styles["entry_date"])]]
                table = Table(rows, colWidths=[usable_width - 39 * mm, 39 * mm], hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 3.5),
                ]))
                story.append(KeepTogether([table]))
                index += 1
            else:
                style = styles["h1"] if block.level == 1 else styles["h3"]
                story.append(Paragraph(rich(block), style))
        elif block.kind == "quote":
            story.append(Paragraph(rich(block), styles["quote"]))
        elif doc.document_type == "cv" and title_seen and block.text == doc.contact_line:
            contact_rule = HRFlowable(width="100%", thickness=0.45, color=colors.HexColor("#D6DADE"), spaceBefore=-8, spaceAfter=2)
            contact_rule._keepWithNext = True
            story.extend([Paragraph(escape(_contact_line(block.text)), styles["contact"]), contact_rule])
        elif (
            doc.document_type == "cv"
            and current_section == "Kompetenzen"
            and _bold_only(block)
            and index + 1 < len(doc.blocks)
            and doc.blocks[index + 1].kind == "paragraph"
        ):
            story.append(KeepTogether([
                Paragraph(rich(block), styles["skill_title"]),
                Paragraph(rich(doc.blocks[index + 1]), styles["skill_values"]),
            ]))
            index += 1
        else:
            story.append(Paragraph(rich(block), styles["body"]))
        index += 1
    pdf = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=17 * mm, bottomMargin=17 * mm, title=doc.title, author="ai-job-suche local export")

    def page(canvas, _doc):
        if preview:
            canvas.saveState()
            canvas.setFillColor(colors.HexColor("#E1E4E8"))
            canvas.setFont(fonts["bold"], 64)
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(30)
            canvas.drawCentredString(0, 0, "DRAFT")
            canvas.restoreState()

    def embedded_font_canvas(filename, *args, **kwargs):
        kwargs.setdefault("initialFontName", fonts["regular"])
        kwargs.setdefault("initialFontSize", 9.8)
        kwargs.setdefault("initialLeading", 13.4)
        return Canvas(filename, *args, **kwargs)

    pdf.build(story, onFirstPage=page, onLaterPages=page, canvasmaker=embedded_font_canvas)


def render_pdf(html_file: Path, output: Path, backend: PdfBackend | None = None, document: StructuredDocument | None = None, preview: bool = False, template_id: str = "") -> PdfBackend:
    backends = [backend] if backend else available_pdf_backends()
    if not backends:
        raise RuntimeError("No PDF backend available. Install/use Chrome or Edge, or add WeasyPrint to the project virtual environment.")
    output.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    for candidate in backends:
        try:
            if output.exists():
                output.unlink()
            if candidate.name in {"chrome", "edge"}:
                command = [candidate.executable, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--no-pdf-header-footer", f"--print-to-pdf={output.resolve()}", html_file.resolve().as_uri()]
                result = subprocess.run(command, capture_output=True, text=True, timeout=60)
                if result.returncode != 0 or not output.exists():
                    raise RuntimeError(f"exit {result.returncode}: {result.stderr.strip()[-800:]}")
            elif candidate.name == "weasyprint":
                from weasyprint import HTML
                HTML(filename=str(html_file)).write_pdf(str(output))
            elif candidate.name == "reportlab":
                if document is None:
                    raise RuntimeError("structured document is required for ReportLab fallback")
                _render_reportlab(document, output, preview, template_id)
            else:
                raise RuntimeError(f"unsupported backend: {candidate.name}")
            size = output.stat().st_size
            if not PDF_MIN_BYTES <= size <= PDF_MAX_BYTES:
                raise RuntimeError(
                    f"generated PDF size {size} bytes is outside the required "
                    f"{PDF_MIN_BYTES}-{PDF_MAX_BYTES} byte range"
                )
            return candidate
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            failures.append(f"{candidate.name}: {exc}")
    raise RuntimeError("All PDF backends failed: " + " | ".join(failures))
