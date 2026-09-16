#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_export.package_builder import ExportRequest, export_documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export application Markdown to ATS-readable Markdown, HTML, DOCX, and PDF.")
    parser.add_argument("--application", type=Path, required=True, help="Application directory containing cv-<lang>.md and/or cover-letter-<lang>.md")
    parser.add_argument("--document", choices=("cv", "cover-letter", "all"), default="all")
    parser.add_argument("--language", choices=("de", "en"), default="de")
    parser.add_argument("--formats", nargs="+", choices=("md", "html", "docx", "pdf"), default=("md", "html", "docx", "pdf"))
    parser.add_argument("--mode", choices=("preview", "final"), default="preview")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing files in exports/ (off by default)")
    parser.add_argument("--force-closed", action="store_true", help="Allow final export for rejected/withdrawn only when explicitly requested; all fact gates still apply")
    parser.add_argument("--output-dir", type=Path, help="Optional output directory; defaults to <application>/exports")
    parser.add_argument("--name-prefix", default="", help="Optional controlled filename prefix, mainly for synthetic demos (for example: sample)")
    parser.add_argument("--template", dest="template_id", default="", help="Resume template id; German CV defaults to german-professional")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = export_documents(ExportRequest(
            application=args.application,
            document=args.document,
            language=args.language,
            formats=tuple(args.formats),
            mode=args.mode,
            overwrite=args.overwrite,
            force_closed=args.force_closed,
            output_dir=args.output_dir,
            name_prefix=args.name_prefix,
            template_id=args.template_id,
        ), PROJECT_ROOT)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for path in result.outputs:
        print(f"CREATED: {path}")
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for blocker in result.blockers:
        print(f"BLOCKED: {blocker}", file=sys.stderr)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if result.report:
        print(f"REPORT: {result.report}")
    return 3 if result.blockers else 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
