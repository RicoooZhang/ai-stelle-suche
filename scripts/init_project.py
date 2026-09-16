#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

DIRECTORIES = [
    "candidate/source-documents", "candidate/profile", "candidate/resumes/de", "candidate/resumes/en",
    "candidate/references", "candidate/certificates", "candidate/private", "candidate/extracted",
    "data/jobs", "data/companies", "data/applications", "data/searches", "data/archive", "data/exports", "data/sample",
    "applications", "reports", "scripts", "skills", ".agents/skills", "tests/fixtures", "docs", "logs",
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="创建缺失的本地项目目录，不覆盖文件")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    for relative in DIRECTORIES:
        target = args.root.resolve() / relative
        target.mkdir(parents=True, exist_ok=True)
        print(f"OK {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
