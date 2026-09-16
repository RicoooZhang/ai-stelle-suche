#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.common import write_json
from job_system.scoring import score_job


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="按 config/scoring.yaml 计算 0-100 匹配分")
    parser.add_argument("job", type=Path, help="包含 dimension_ratings 的岗位 JSON")
    parser.add_argument("--write", action="store_true", help="备份后写回原文件")
    args = parser.parse_args(argv)
    try:
        job = json.loads(args.job.read_text(encoding="utf-8-sig"))
        result = score_job(job)
        if args.write:
            job.update(result)
            write_json(args.job, job, overwrite=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
