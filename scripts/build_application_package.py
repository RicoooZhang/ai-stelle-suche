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
    parser = argparse.ArgumentParser(description="Build a complete local application export package without sending or uploading it.")
    parser.add_argument("--application", type=Path, required=True)
    parser.add_argument("--language", choices=("de", "en"), default="de")
    parser.add_argument("--mode", choices=("preview", "final"), default="preview")
    parser.add_argument("--formats", nargs="+", choices=("md", "html", "docx", "pdf"), default=("md", "html", "docx", "pdf"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--force-closed", action="store_true")
    parser.add_argument("--template", dest="template_id", default="", help="Resume template id; German CV defaults to german-professional")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = export_documents(ExportRequest(
            application=args.application, document="all", language=args.language,
            formats=tuple(args.formats), mode=args.mode, overwrite=args.overwrite,
            force_closed=args.force_closed, template_id=args.template_id,
        ), PROJECT_ROOT)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for path in result.outputs:
        print(f"CREATED: {path}")
    for message in result.blockers:
        print(f"BLOCKED: {message}", file=sys.stderr)
    for message in result.errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in result.warnings:
        print(f"WARNING: {message}", file=sys.stderr)
    return 3 if result.blockers else 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
