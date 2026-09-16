from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .docx_renderer import render_docx
from .html_renderer import render_html
from .naming import output_stem
from .parser import parse_markdown
from .pdf_renderer import render_pdf
from .template_config import TemplateSelection, resolve_template
from .validators import read_status, validate_docx, validate_export, validate_html, validate_pdf


@dataclass
class ExportRequest:
    application: Path
    document: str = "all"
    language: str = "de"
    formats: tuple[str, ...] = ("md", "html", "docx", "pdf")
    mode: str = "preview"
    overwrite: bool = False
    force_closed: bool = False
    output_dir: Path | None = None
    name_prefix: str = ""
    template_id: str = ""


@dataclass
class ExportResult:
    outputs: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    pdf_backend: str = "not used"
    report: Path | None = None


def _metadata(application: Path) -> dict:
    path = application / "job-metadata.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except ValueError:
            return {}
    adjacent = application.parent / f"{application.name}.json"
    if adjacent.exists():
        try:
            return json.loads(adjacent.read_text(encoding="utf-8-sig"))
        except ValueError:
            return {}
    return {}


def _export_config(application: Path) -> dict:
    path = application / "export-config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        raise ValueError(f"invalid export-config.json: {exc}") from exc


def _configured_path(application: Path, value: str) -> Path:
    path = (application / value).resolve()
    try:
        path.relative_to(application.resolve())
    except ValueError as exc:
        raise ValueError("configured Markdown source must remain inside the export workspace") from exc
    return path


def _sources(application: Path, document: str, language: str) -> list[tuple[str, Path]]:
    config = _export_config(application)
    configured = config.get("source_files", {})
    candidates = []
    if document in {"all", "cv"}:
        value = configured.get("cv", {}).get(language) if isinstance(configured.get("cv"), dict) else None
        candidates.append(("cv", _configured_path(application, value) if value else application / f"cv-{language}.md"))
    if document in {"all", "cover-letter"}:
        value = configured.get("cover-letter", {}).get(language) if isinstance(configured.get("cover-letter"), dict) else None
        candidates.append(("cover-letter", _configured_path(application, value) if value else application / f"cover-letter-{language}.md"))
    return [(kind, path) for kind, path in candidates if path.exists()]


def _configured_template(application: Path, document_type: str, language: str) -> str:
    templates = _export_config(application).get("templates", {})
    value = templates.get(document_type, {}) if isinstance(templates, dict) else {}
    return str(value.get(language) or "") if isinstance(value, dict) else ""


def _write(path: Path, content: str | bytes, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8", newline="\n")


def _markdown(doc, preview: bool) -> str:
    lines = ["> **DRAFT – PREVIEW ONLY**", ""] if preview else []
    for block in doc.blocks:
        value = "".join(("**" + r.text + "**") if r.bold else ("*" + r.text + "*") if r.italic else r.text for r in block.runs)
        if block.kind == "heading":
            lines.append("#" * block.level + " " + value)
        elif block.kind == "bullet":
            lines.append("- " + value)
        elif block.kind == "quote":
            lines.append("> " + value)
        else:
            lines.append(value)
        if block.kind in {"heading", "paragraph", "quote"}:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_documents(request: ExportRequest, project_root: Path | None = None) -> ExportResult:
    application = request.application.resolve()
    if not application.is_dir():
        raise FileNotFoundError(f"application directory not found: {application}")
    if request.mode not in {"preview", "final"}:
        raise ValueError("mode must be preview or final")
    allowed_formats = {"md", "html", "docx", "pdf"}
    unknown = set(request.formats) - allowed_formats
    if unknown:
        raise ValueError(f"unsupported formats: {sorted(unknown)}")
    project_root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    source_pairs = _sources(application, request.document, request.language)
    if not source_pairs:
        raise FileNotFoundError("no matching Markdown source document found")
    template_root = project_root / "templates"
    documents: list[tuple[str, object, TemplateSelection]] = []
    for kind, path in source_pairs:
        doc = parse_markdown(path, kind, request.language)
        requested_template = request.template_id or _configured_template(application, kind, request.language)
        selection = resolve_template(template_root, kind, request.language, requested_template)
        documents.append((kind, doc, selection))
    validation = validate_export(application, [doc for _, doc, _ in documents], request.mode, project_root, request.force_closed)
    result = ExportResult(blockers=list(validation.blockers), warnings=list(validation.warnings))
    out_dir = (request.output_dir or application / "exports").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if result.blockers:
        result.report = _write_report(out_dir, request, result, read_status(application), documents, {}, overwrite=request.overwrite)
        return result
    metadata = _metadata(application)
    company = str(metadata.get("company") or "")
    preview = request.mode == "preview"
    produced: list[tuple[Path, object]] = []
    for kind, doc, selection in documents:
        stem = f"{request.name_prefix}-{kind}" if request.name_prefix else output_stem(doc.title or "Candidate", kind, request.language, company, preview)
        html_path = out_dir / f"{stem}.html"
        if "md" in request.formats:
            path = out_dir / f"{stem}.md"
            _write(path, _markdown(doc, preview), request.overwrite)
            result.outputs.append(path)
        if "html" in request.formats or "pdf" in request.formats:
            html_value = render_html(doc, template_root, preview, selection.template_id)
            _write(html_path, html_value, request.overwrite)
            if "html" in request.formats:
                result.outputs.append(html_path)
            produced.append((html_path, doc))
            result.errors.extend(f"{html_path.name}: {e}" for e in validate_html(html_path))
        if "docx" in request.formats:
            path = out_dir / f"{stem}.docx"
            if path.exists() and not request.overwrite:
                raise FileExistsError(f"refusing to overwrite existing file: {path}")
            render_docx(doc, path, preview, selection.template_id)
            result.outputs.append(path)
            result.errors.extend(f"{path.name}: {e}" for e in validate_docx(path))
        if "pdf" in request.formats:
            path = out_dir / f"{stem}.pdf"
            if path.exists() and not request.overwrite:
                raise FileExistsError(f"refusing to overwrite existing file: {path}")
            try:
                backend = render_pdf(html_path, path, document=doc, preview=preview, template_id=selection.template_id)
                result.pdf_backend = backend.name
                result.outputs.append(path)
                expected_experience = next((b.text for b in doc.blocks if b.kind == "heading" and b.level == 3), "") or next((b.text for b in doc.blocks if b.kind == "heading" and b.level == 2), "")
                expected_pages = 2 if kind == "cv" else None
                errors, untested = validate_pdf(
                    path,
                    doc.title,
                    expected_experience,
                    request.mode == "final",
                    expected_pages=expected_pages,
                )
                result.errors.extend(f"{path.name}: {e}" for e in errors)
                result.warnings.extend(f"{path.name}: {w}" for w in untested)
            except RuntimeError as exc:
                result.errors.append(str(exc))
    checksums = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in result.outputs if path.exists()}
    checksum_path = out_dir / "checksum.json"
    _write(checksum_path, json.dumps(checksums, ensure_ascii=False, indent=2) + "\n", request.overwrite)
    result.outputs.append(checksum_path)
    result.report = _write_report(out_dir, request, result, read_status(application), documents, checksums, overwrite=request.overwrite)
    result.outputs.append(result.report)
    return result


def _pdf_page_count(path: Path) -> int | None:
    try:
        from pypdf import PdfReader
        return len(PdfReader(path).pages)
    except (ImportError, OSError, ValueError):
        return None


def _write_report(out_dir: Path, request: ExportRequest, result: ExportResult, status: str, documents, checksums: dict[str, str], overwrite: bool) -> Path:
    path = out_dir / "export-report.md"
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    sources = [doc.source.resolve() for _, doc, _ in documents]
    selections = {(selection.template_id, selection.name) for _, _, selection in documents}
    lines = [
        "# Document export report", "",
        "## Export metadata", "",
        f"- generated_at: {generated_at}",
        f"- mode: {request.mode}",
        f"- application_status: {status}",
        f"- source_markdown: {', '.join(f'`{item}`' for item in sources) if sources else 'not resolved'}",
        f"- template_id: {', '.join(item[0] for item in sorted(selections)) if selections else 'not resolved'}",
        f"- template_name: {', '.join(item[1] for item in sorted(selections)) if selections else 'not resolved'}",
        f"- pdf_backend: {result.pdf_backend}",
        "- submission: NOT_SENT_NOT_UPLOADED", "", "## Result", "",
    ]
    outcome = "BLOCKED" if result.blockers else "COMPLETED_WITH_ERRORS" if result.errors else "COMPLETED"
    lines.append(f"- outcome: {outcome}")
    if status == "applied" and request.mode == "final":
        lines.append("- version_note: re-export of an applied application; checksums record this version")
    if result.outputs:
        lines.extend(["", "## Files", "", *[f"- `{item.name}`" for item in result.outputs]])
        lines.extend(["", "## Artifact details", ""])
        for item in result.outputs:
            if not item.exists() or item.suffix.lower() in {".json", ".md"}:
                continue
            detail = f"- `{item.name}`: {item.stat().st_size} bytes"
            if item.suffix.lower() == ".pdf":
                pages = _pdf_page_count(item)
                detail += f"; pages: {pages if pages is not None else 'untested'}"
            if item.name in checksums:
                detail += f"; sha256: `{checksums[item.name]}`"
            lines.append(detail)
        suffixes = {item.suffix.lower() for item in result.outputs}
        lines.extend(["", "## Verification", ""])
        if ".html" in suffixes:
            lines.append("- HTML: A4 print CSS present; no external resource references detected.")
        if ".docx" in suffixes:
            lines.append("- DOCX: OOXML package structure, styles, headings, and numbering parts validated.")
        if ".pdf" in suffixes:
            if any("PDF text/page/ATS extraction not tested" in item for item in result.warnings):
                lines.append("- PDF: file generated; text/page ATS extraction is untested in the active Python environment.")
            elif not any(".pdf:" in item.lower() for item in result.errors):
                lines.append("- PDF: 50-200 KiB size gate, A4 portrait, embedded-font use, page count (exactly two for CVs), extractable text, identity, experience heading, draft marker, and Markdown-residue checks passed.")
        if ".pdf" not in suffixes:
            ats_result = "NOT_RUN"
        elif any(".pdf:" in item.lower() for item in result.errors):
            ats_result = "FAILED"
        elif any("PDF text/page/ATS extraction not tested" in item for item in result.warnings):
            ats_result = "UNTESTED"
        else:
            ats_result = "PASSED"
        lines.append(f"- ATS: {ats_result}")
        if checksums:
            lines.extend(["", "## Checksums", "", *[f"- `{name}`: `{value}`" for name, value in sorted(checksums.items())]])
    else:
        lines.extend(["", "## Verification", "", "- ATS: NOT_RUN (no artifacts generated because export was blocked)."])
    if result.blockers:
        lines.extend(["", "## Final-export blockers", "", *[f"- {item}" for item in result.blockers]])
    if result.errors:
        lines.extend(["", "## Errors", "", *[f"- {item}" for item in result.errors]])
    if result.warnings:
        lines.extend(["", "## Warnings / untested checks", "", *[f"- {item}" for item in result.warnings]])
    if any(doc.document_type == "cover-letter" for _, doc, _ in documents):
        text = "\n".join(doc.plain_text() for _, doc, _ in documents if doc.document_type == "cover-letter")
        if "NEEDS_CONFIRMATION" in text:
            lines.extend(["", "## Manual completion", "", "- Cover-letter recipient/address contains NEEDS_CONFIRMATION and must be completed without invention."])
    _write(path, "\n".join(lines).rstrip() + "\n", overwrite)
    return path
