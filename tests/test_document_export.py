from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from document_export.docx_renderer import render_docx
from document_export.html_renderer import render_html
from document_export.models import Block, InlineRun
from document_export.naming import output_stem, safe_component
from document_export.package_builder import ExportRequest, export_documents
from document_export.parser import parse_markdown
from document_export.pdf_renderer import PDF_MAX_BYTES, PDF_MIN_BYTES, PdfBackend, render_pdf, select_pdf_backend
from document_export.template_config import DEFAULT_GERMAN_CV_TEMPLATE, resolve_template
from document_export.validators import validate_docx, validate_export, validate_html, validate_pdf

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "document-export-application"


def extend_sample_cv_to_two_pages(doc):
    for index in range(18):
        doc.blocks.append(Block("bullet", runs=(InlineRun(f"Zusätzliche synthetische Prüfzeile {index + 1}: SAMPLE_DATA_NOT_REAL."),)))
    return doc


class DocumentExportTests(unittest.TestCase):
    def test_german_professional_is_default_for_german_cv(self):
        selection = resolve_template(ROOT / "templates", "cv", "de")
        self.assertEqual(selection.template_id, DEFAULT_GERMAN_CV_TEMPLATE)
        config = json.loads((selection.path / "template.json").read_text(encoding="utf-8"))
        self.assertEqual(config["page"]["size"], "A4")
        self.assertEqual(config["page"]["maximum_pages"], 2)
        self.assertTrue(config["ats_compatibility"]["single_column"])

    def test_markdown_structure_parser(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        self.assertEqual(doc.title, "SAMPLE_DATA_NOT_REAL")
        self.assertIn("Berufserfahrung", [b.text for b in doc.blocks if b.kind == "heading"])
        self.assertTrue(any(b.kind == "bullet" for b in doc.blocks))

    def test_draft_hint_is_filtered(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        self.assertEqual(doc.draft_markers_removed, 1)
        self.assertNotIn("ENTWURF", doc.plain_text())

    def test_preview_filename(self):
        self.assertTrue(output_stem("SAMPLE_DATA_NOT_REAL", "cv", "de", "Example GmbH", True).endswith("DRAFT"))

    def test_windows_filename_sanitization(self):
        value = safe_component('CON:<bad>|name?* .')
        self.assertNotRegex(value, r'[<>:"/\\|?*]')
        self.assertLessEqual(len(value), 48)

    def test_final_requires_approved(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        result = validate_export(FIXTURE, [doc], "final", ROOT)
        self.assertFalse(result.passed)
        self.assertTrue(any("approved/applied" in b for b in result.blockers))

    def test_not_supported_blocks_final(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp) / "app"
            app.mkdir()
            (app / "status.md").write_text("- status: approved\n", encoding="utf-8")
            (app / "fact-check.md").write_text("NOT_SUPPORTED\n", encoding="utf-8")
            (app / "source-traceability.md").write_text("VERIFIED\n", encoding="utf-8")
            profile = Path(tmp) / "candidate" / "profile"
            profile.mkdir(parents=True)
            (profile / "do-not-claim.md").write_text("clear\n", encoding="utf-8")
            (profile / "profile-conflicts.md").write_text("clear\n", encoding="utf-8")
            doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
            result = validate_export(app, [doc], "final", Path(tmp))
            self.assertTrue(any("NOT_SUPPORTED" in b for b in result.blockers))

    def test_html_has_a4_and_no_external_resources(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.html"
            path.write_text(render_html(doc, ROOT / "templates", True), encoding="utf-8")
            self.assertEqual(validate_html(path), [])
            self.assertIn("size: A4", path.read_text(encoding="utf-8"))

    def test_german_professional_contact_sections_and_date_layout(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        html = render_html(doc, ROOT / "templates", True)
        self.assertIn('data-template-id="german-professional"', html)
        self.assertIn("Musterstadt | sample@example.invalid | +49 000 000000", html)
        self.assertNotRegex(html, r'class="contact-line"[^>]*>[^<]*<br')
        self.assertIn('class="entry-date">01/2024–12/2025', html)
        order = [html.index(label) for label in ("Profil", "Berufserfahrung", "Projekte", "Kompetenzen", "Ausbildung", "Sprachen")]
        self.assertEqual(order, sorted(order))
        self.assertIn("grid-column: 2", html)

    def test_preview_has_draft_and_final_has_no_visible_draft_marker(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        preview = render_html(doc, ROOT / "templates", True)
        final = render_html(doc, ROOT / "templates", False)
        self.assertIn('<div class="draft-watermark"', preview)
        self.assertNotIn('<div class="draft-watermark"', final)
        self.assertNotIn("ENTWURF", final.split("</style>", 1)[-1])


    def test_docx_structure_and_real_numbering(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.docx"
            render_docx(doc, path, True)
            self.assertEqual(validate_docx(path), [])
            with ZipFile(path) as archive:
                self.assertIn("word/numbering.xml", archive.namelist())
                self.assertIn("SAMPLE_DATA_NOT_REAL", archive.read("word/document.xml").decode("utf-8"))

    def test_docx_uses_editable_structure_and_right_aligned_dates(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.docx"
            render_docx(doc, path, True, DEFAULT_GERMAN_CV_TEMPLATE)
            self.assertEqual(validate_docx(path), [])
            with ZipFile(path) as archive:
                xml = archive.read("word/document.xml").decode("utf-8")
                styles = archive.read("word/styles.xml").decode("utf-8")
                self.assertIn('w:val="right"', xml)
                self.assertIn('w:styleId="Contact"', styles)
                self.assertIn("Musterstadt | sample@example.invalid | +49 000 000000", xml)
                self.assertNotIn("<w:tbl>", xml)

    def test_pdf_backend_selection(self):
        backend = select_pdf_backend()
        if backend:
            self.assertIn(backend.name, {"chrome", "edge", "weasyprint", "reportlab"})

    def test_missing_pdf_backend_error(self):
        with tempfile.TemporaryDirectory() as tmp, patch("document_export.pdf_renderer.available_pdf_backends", return_value=[]):
            html = Path(tmp) / "x.html"
            html.write_text("<html></html>", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "No PDF backend"):
                render_pdf(html, Path(tmp) / "x.pdf")

    def test_reportlab_final_is_a4_extractable_and_has_no_draft_markers(self):
        try:
            from pypdf import PdfReader
            import reportlab  # noqa: F401
        except ImportError:
            self.skipTest("reportlab/pypdf not installed")
        doc = extend_sample_cv_to_two_pages(parse_markdown(FIXTURE / "cv-de.md", "cv", "de"))
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "sample.html"
            pdf_path = Path(tmp) / "sample.pdf"
            html_path.write_text(render_html(doc, ROOT / "templates", False), encoding="utf-8")
            render_pdf(html_path, pdf_path, PdfBackend("reportlab"), doc, False, DEFAULT_GERMAN_CV_TEMPLATE)
            reader = PdfReader(pdf_path)
            self.assertEqual(len(reader.pages), 2)
            self.assertGreaterEqual(pdf_path.stat().st_size, PDF_MIN_BYTES)
            self.assertLessEqual(pdf_path.stat().st_size, PDF_MAX_BYTES)
            page = reader.pages[0]
            self.assertAlmostEqual(float(page.mediabox.width), 595.28, delta=1)
            self.assertAlmostEqual(float(page.mediabox.height), 841.89, delta=1)
            text = "\n".join(item.extract_text() or "" for item in reader.pages)
            self.assertIn("SAMPLE_DATA_NOT_REAL", text)
            self.assertIn("Äußere Größe", text)
            self.assertNotRegex(text, r"(?i)\b(?:draft|entwurf|preview)\b")
            errors, _ = validate_pdf(pdf_path, doc.title, "Sample Analyst · Example GmbH", True, expected_pages=2)
            self.assertEqual(errors, [])

    def test_reportlab_preview_pdf_contains_draft_watermark_text(self):
        try:
            from pypdf import PdfReader
            import reportlab  # noqa: F401
        except ImportError:
            self.skipTest("reportlab/pypdf not installed")
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "sample.html"
            pdf_path = Path(tmp) / "sample.pdf"
            html_path.write_text(render_html(doc, ROOT / "templates", True), encoding="utf-8")
            render_pdf(html_path, pdf_path, PdfBackend("reportlab"), doc, True, DEFAULT_GERMAN_CV_TEMPLATE)
            text = "\n".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)
            self.assertIn("DRAFT", text)

    def test_final_pdf_validation_rejects_preview_marker(self):
        try:
            import reportlab  # noqa: F401
        except ImportError:
            self.skipTest("reportlab not installed")
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        doc.blocks.append(Block("paragraph", runs=(InlineRun("PREVIEW"),)))
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "sample.html"
            pdf_path = Path(tmp) / "sample.pdf"
            html_path.write_text(render_html(doc, ROOT / "templates", False), encoding="utf-8")
            render_pdf(html_path, pdf_path, PdfBackend("reportlab"), doc, False, DEFAULT_GERMAN_CV_TEMPLATE)
            errors, _ = validate_pdf(pdf_path, doc.title, "Sample Analyst · Example GmbH", True)
            self.assertTrue(any("preview/test watermark" in item for item in errors))

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out"
            request = ExportRequest(FIXTURE, "cv", "de", ("html",), "preview", output_dir=output)
            first = export_documents(request, ROOT)
            self.assertFalse(first.errors)
            with self.assertRaises(FileExistsError):
                export_documents(request, ROOT)

    def test_german_characters_preserved(self):
        doc = parse_markdown(FIXTURE / "cv-de.md", "cv", "de")
        html = render_html(doc, ROOT / "templates")
        self.assertIn("Äußere Größe", html)

    def test_export_report_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = export_documents(ExportRequest(FIXTURE, "cv", "de", ("md",), "preview", output_dir=Path(tmp)), ROOT)
            self.assertTrue(result.report and result.report.exists())
            self.assertIn("NOT_SENT_NOT_UPLOADED", result.report.read_text(encoding="utf-8"))

    def test_approved_direct_source_final_uses_default_template_without_mutating_markdown(self):
        try:
            import reportlab  # noqa: F401
        except ImportError:
            self.skipTest("reportlab not installed")
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp) / "direct-cv"
            app.mkdir()
            source = app / "custom-source.md"
            shutil.copyfile(FIXTURE / "cv-de.md", source)
            with source.open("a", encoding="utf-8") as stream:
                stream.write("\n\n" + "\n".join(
                    f"- Zusätzliche synthetische Prüfzeile {index + 1}: SAMPLE_DATA_NOT_REAL."
                    for index in range(18)
                ) + "\n")
            (app / "export-config.json").write_text(json.dumps({
                "source_files": {"cv": {"de": "custom-source.md"}},
                "templates": {"cv": {"de": "german-professional"}},
            }), encoding="utf-8")
            (app / "status.md").write_text("- status: approved\n", encoding="utf-8")
            (app / "fact-check.md").write_text("SUPPORTED\n", encoding="utf-8")
            (app / "source-traceability.md").write_text("All fixture claims traced.\n", encoding="utf-8")
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            out = app / "final-v1"
            with patch("document_export.pdf_renderer.available_pdf_backends", return_value=[PdfBackend("reportlab")]):
                result = export_documents(ExportRequest(app, "cv", "de", ("html", "docx", "pdf"), "final", output_dir=out), ROOT)
            self.assertFalse(result.blockers)
            self.assertFalse(result.errors)
            self.assertEqual(before, hashlib.sha256(source.read_bytes()).hexdigest())
            names = {path.name for path in result.outputs}
            self.assertTrue(any(name.endswith(".pdf") and "DRAFT" not in name for name in names))
            html_path = next(path for path in result.outputs if path.suffix == ".html")
            html = html_path.read_text(encoding="utf-8")
            self.assertNotIn('<div class="draft-watermark"', html)
            self.assertNotRegex(html.split("</style>", 1)[-1], r"(?i)\b(?:draft|entwurf|preview)\b")
            docx_path = next(path for path in result.outputs if path.suffix == ".docx")
            with ZipFile(docx_path) as archive:
                visible_xml = archive.read("word/document.xml").decode("utf-8")
            self.assertNotRegex(visible_xml, r"(?i)\b(?:draft|entwurf|preview)\b")
            report = result.report.read_text(encoding="utf-8")
            self.assertIn("template_id: german-professional", report)
            self.assertIn("source_markdown:", report)
            self.assertIn("pages:", report)
            self.assertIn("embedded-font use", report)
            self.assertIn("50-200 KiB size gate", report)
            self.assertIn("ATS: PASSED", report)
            self.assertIn("sha256:", report)

    def test_skill_declares_german_professional_default_for_new_sessions(self):
        canonical = (ROOT / "skills/export-application-documents/SKILL.md").read_text(encoding="utf-8")
        discovery = (ROOT / ".agents/skills/export-application-documents/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Use `german-professional` for every German CV", canonical)
        self.assertIn("templates/resume/templates.json", canonical)
        self.assertIn("german-professional", discovery)
        self.assertIn("50-200 KiB", canonical)
        self.assertIn("exactly two PDF pages", canonical)
        self.assertIn("embedded-font", discovery)

    def test_sample_data_isolated(self):
        fixture_text = "\n".join(path.read_text(encoding="utf-8") for path in FIXTURE.glob("*.md"))
        self.assertIn("SAMPLE_DATA_NOT_REAL", fixture_text)
        self.assertIn("example.invalid", fixture_text)

    def test_final_block_creates_report_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = export_documents(ExportRequest(FIXTURE, "cv", "de", ("docx",), "final", output_dir=Path(tmp)), ROOT)
            self.assertTrue(result.blockers)
            self.assertTrue(result.report and result.report.exists())
            self.assertFalse(any(path.suffix == ".docx" for path in result.outputs))
            self.assertIn("ATS: NOT_RUN", result.report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
