#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.candidate import import_documents
from job_system.common import write_text


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="本地导入候选人材料，原文件只读且不上传")
    parser.add_argument("--source", type=Path, default=root / "candidate/source-documents")
    parser.add_argument("--output", type=Path, default=root / "candidate/extracted")
    args = parser.parse_args(argv)
    try:
        results = import_documents(args.source, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not results:
        print("未发现待导入文件。请将原始材料放入 candidate/source-documents/。")
        return 0
    index_path = root / "candidate/profile/source-index.md"
    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Source Index\n\n| Fact ID | Fact | Status | Source file | Location/page | Extracted on | Notes |\n|---|---|---|---|---|---|---|\n"
    for result in results:
        print(f"{result['source_file']}: {result['status']} — {'; '.join(result['warnings'])}")
        marker = result["sha256"][:12]
        if marker not in index_text:
            safe_name = result["source_file"].replace("|", "\\|")
            index_text += f"| DOC-{marker} | Document imported; atomic facts pending review | {result['status']} | {safe_name} | whole file | {result['extracted_on']} | sha256:{marker} |\n"
    write_text(index_path, index_text, overwrite=index_path.exists())
    print(f"已更新来源索引: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
