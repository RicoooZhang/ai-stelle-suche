#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.common import write_json
from job_system.job_parser import parse_job_text, validate_job_record
from job_system.scoring import score_job


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="分析本地岗位正文或 JSON；不登录、不投递")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="粘贴的岗位正文")
    group.add_argument("--file", type=Path, help="UTF-8 正文或 JSON 文件")
    parser.add_argument("--url", default="", help="来源 URL（只记录，不自动访问）")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--ratings", type=Path, help="人工确认的维度评分 JSON；不提供则不计算匹配分")
    parser.add_argument("--save", action="store_true", help="保存到 data/jobs/")
    args = parser.parse_args(argv)
    try:
        if args.file:
            raw = args.file.read_text(encoding="utf-8-sig")
            job = json.loads(raw) if args.file.suffix.casefold() == ".json" else parse_job_text(raw, source_url=args.url, source=args.source)
        else:
            job = parse_job_text(args.text, source_url=args.url, source=args.source)
        if args.ratings:
            ratings = json.loads(args.ratings.read_text(encoding="utf-8-sig"))
            job["dimension_ratings"] = ratings.get("dimension_ratings", ratings)
            job["risk_flags"] = ratings.get("risk_flags", [])
            job.update(score_job(job))
        errors = validate_job_record(job)
        if errors:
            raise ValueError("; ".join(errors))
        if args.save:
            output = root / "data/jobs" / f"{job['job_id']}.json"
            write_json(output, job)
            print(f"已保存: {output}")
        print(json.dumps(job, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
