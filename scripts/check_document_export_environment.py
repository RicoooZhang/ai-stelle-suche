#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_export.pdf_renderer import available_pdf_backends, select_pdf_backend


def _first_existing(paths: list[Path]) -> str | None:
    return next((str(path) for path in paths if path.is_file()), None)


def inspect_environment() -> dict:
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    local_app = Path(os.environ.get("LOCALAPPDATA", ""))
    paths = {
        "microsoft_word": [program_files / "Microsoft Office/root/Office16/WINWORD.EXE", program_files_x86 / "Microsoft Office/root/Office16/WINWORD.EXE"],
        "libreoffice": [program_files / "LibreOffice/program/soffice.exe", program_files_x86 / "LibreOffice/program/soffice.exe"],
        "chrome": [program_files / "Google/Chrome/Application/chrome.exe", program_files_x86 / "Google/Chrome/Application/chrome.exe", local_app / "Google/Chrome/Application/chrome.exe"],
        "edge": [program_files_x86 / "Microsoft/Edge/Application/msedge.exe", program_files / "Microsoft/Edge/Application/msedge.exe", local_app / "Microsoft/Edge/Application/msedge.exe"],
    }
    executables = {}
    for key, candidates in paths.items():
        command_name = {"microsoft_word": "WINWORD", "libreoffice": "soffice"}.get(key, key)
        executables[key] = shutil.which(command_name) or shutil.which(command_name + ".exe") or _first_existing(candidates)
    for key in ("pandoc", "wkhtmltopdf", "typst"):
        executables[key] = shutil.which(key) or shutil.which(key + ".exe")
    modules = {name: bool(importlib.util.find_spec(name)) for name in ("docx", "weasyprint", "playwright", "pypdf", "pdfplumber", "reportlab", "jinja2")}
    backend = select_pdf_backend()
    return {
        "python": sys.version.split()[0],
        "project_root": str(PROJECT_ROOT),
        "executables": executables,
        "python_modules": modules,
        "selected_pdf_backend": None if backend is None else {"name": backend.name, "path": backend.executable or None},
        "available_pdf_backends": [{"name": item.name, "path": item.executable or None} for item in available_pdf_backends()],
        "implementation": {
            "html": "Python standard library + local CSS",
            "docx": "Python standard library OOXML ZIP writer (no global dependency)",
            "pdf": "HTML + Chrome/Edge headless; optional WeasyPrint; ReportLab structured-document fallback",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect installed local document export backends without installing or changing anything.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)
    data = inspect_environment()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"Python: {data['python']}")
        for name, value in data["executables"].items():
            print(f"{name}: {value or 'NOT FOUND'}")
        for name, value in data["python_modules"].items():
            print(f"python-{name}: {'AVAILABLE' if value else 'NOT FOUND'}")
        backend = data["selected_pdf_backend"]
        print(f"selected PDF backend: {backend['name'] + ' (' + str(backend['path']) + ')' if backend else 'NONE'}")
    return 0 if data["selected_pdf_backend"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
