---
name: export-application-documents
description: Export saved German or English application CV and cover-letter Markdown into safe preview or approved final Markdown, HTML, DOCX, and PDF packages. Use when the user asks to export application documents, create a preview/final package, generate a German CV with the default german-professional template, generate only a CV or cover-letter PDF/DOCX, re-export an applied package, or diagnose a blocked final export.
---

# Export application documents

1. Read root `AGENTS.md`, the target application directory, `status.md` or job metadata, `fact-check.md`, `source-traceability.md`, `candidate/profile/do-not-claim.md`, and `candidate/profile/profile-conflicts.md`.
2. Never edit source Markdown. Never send, upload, submit, log in, or change application status.
3. Use preview mode for `draft`, `preparing`, and `ready_for_review`; preview filenames contain `DRAFT` or carry a visible DRAFT watermark.
4. Use final mode only for `approved` or `applied`. Require explicit `--force-closed` for `rejected` or `withdrawn`; fact gates still apply.
5. Block final export on missing required review files, `NOT_SUPPORTED`, `DO_NOT_USE`, unresolved `CONFLICTING`, critical `NEEDS_CONFIRMATION`, or forbidden personal fields. Report blockers; never bypass them.
6. Run `python scripts/check_document_export_environment.py`, then invoke `scripts/export_documents.py` or `scripts/build_application_package.py` with the requested document, language, formats, and mode.
7. Do not overwrite exports unless the user explicitly requests `--overwrite`. Keep `export-report.md` and `checksum.json` with successful packages.
8. Verify HTML is self-contained and A4, DOCX is valid OOXML with headings and real numbering, and each PDF is 50-200 KiB, A4 portrait, uses embedded local TrueType fonts, has extractable text, and contains expected identity/experience text. CV PDFs must be exactly two pages. Verify final output contains no `DRAFT`, `ENTWURF`, `preview`, or test watermark. Treat any failed size, page, font, or ATS check as an export error; never pad PDFs with junk data or rasterize text merely to increase file size. Clearly mark unavailable checks as untested.
9. For missing recipient/contact/address data, preserve `NEEDS_CONFIRMATION` in previews and list the manual completion in the report; never invent it.
10. Keep `export-report.md` evidence-rich: record source Markdown, template id/name, mode, generation time, PDF page count and size, checksums, ATS result, status, backend, and submission boundary.
11. Return generated local paths and distinguish completed, blocked, failed, and untested checks. Remind the user that final submission is always manual.

## German CV default template

- Resolve template defaults from `templates/resume/templates.json`.
- Use `german-professional` for every German CV when no template is supplied.
- Treat `templates/resume/german-professional/template.json` as the canonical layout-token and ATS contract.
- Use the same layout for preview and final. Preview must show `DRAFT`; final must show no watermark or draft marker.
- Keep A4 single-column reading order, one-line pipe-separated contact data, consistent ruled section headings, prominent role/company with right-aligned dates, grouped skills, editable DOCX, self-contained HTML, selectable PDF text, and exactly two PDF pages.
- Embed Arial when available; otherwise embed a metrically compatible local TrueType sans-serif family. The PDF size gate is 50-200 KiB (51,200-204,800 bytes). Missing fonts, unembedded fonts, non-A4 pages, page-count drift, or a size outside the gate must fail the export.
- Never add photos, icons, skill bars, complex sidebars, external fonts, CDNs, or hidden ATS text.
- Do not reorder or rewrite Markdown facts to satisfy layout. Report a page-budget problem instead of shrinking body text below the configured minimum.

## Direct candidate CV workspaces

- If `export-config.json` exists, resolve the Markdown source and template from it; keep the configured source inside that workspace.
- Continue to require the workspace `status.md`, `fact-check.md`, and `source-traceability.md` for final mode.
- Do not infer approval from a request to improve templates or create a final. Only an explicit `approved`/`applied` status satisfies the final gate.

Examples:

```powershell
python scripts/export_documents.py --application ".\applications\<company>\<job-title>" --document cv --language de --formats html docx pdf --mode preview
python scripts/export_documents.py --application ".\applications\<company>\<job-title>" --document all --language de --formats docx pdf --mode final
python scripts/build_application_package.py --application ".\applications\<company>\<job-title>" --mode final
python scripts/export_documents.py --application ".\candidate\resumes\de" --document cv --language de --formats html docx pdf --mode preview
python scripts/export_documents.py --application ".\candidate\resumes\de" --document cv --language de --formats html docx pdf --mode final --template german-professional
```
