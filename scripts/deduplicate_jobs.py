#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.common import write_json
from job_system.dedup import find_duplicates


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="识别重复岗位并保留所有来源，不删除记录")
    parser.add_argument("--jobs-dir", type=Path, default=root / "data/jobs")
    parser.add_argument("--threshold", type=float, default=0.84)
    parser.add_argument("--write", action="store_true", help="备份后写入 duplicate_of/all_source_urls")
    args = parser.parse_args(argv)
    try:
        paths = sorted(args.jobs_dir.glob("*.json"))
        jobs = [json.loads(p.read_text(encoding="utf-8-sig")) for p in paths]
        results = find_duplicates(jobs, args.threshold)
        for path, result in zip(paths, results):
            if args.write:
                write_json(path, result, overwrite=True)
            if result.get("duplicate_of"):
                print(f"DUPLICATE {result.get('job_id')} -> {result['duplicate_of']}")
        print(f"检查 {len(results)} 条，重复 {sum(bool(x.get('duplicate_of')) for x in results)} 条")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
