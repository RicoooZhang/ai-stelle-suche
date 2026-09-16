#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.facts import blocked_claims_in_material, validate_fact_records


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="验证正式材料不包含未支持或禁止使用的事实")
    parser.add_argument("material", type=Path, help="待核查 Markdown/TXT 材料")
    parser.add_argument("facts", type=Path, help="事实 JSON 数组：claim/status/source")
    args = parser.parse_args(argv)
    try:
        records = json.loads(args.facts.read_text(encoding="utf-8-sig"))
        errors = validate_fact_records(records)
        violations = blocked_claims_in_material(args.material.read_text(encoding="utf-8-sig"), records)
        if errors or violations:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            for item in violations:
                print(f"BLOCKED: {item['status']} — {item['claim']}", file=sys.stderr)
            return 2
        print("PASS: 未发现被禁止的事实状态。仍需人工审核表达与遗漏。")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
