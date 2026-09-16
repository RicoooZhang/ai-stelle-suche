#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.application import create_application_workspace


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="为岗位创建草稿申请工作区；不会发送、上传或投递")
    parser.add_argument("job", type=Path, help="岗位 JSON")
    parser.add_argument("--force-level", choices=list("ABCDE"), help="用户明确要求时覆盖默认材料级别")
    args = parser.parse_args(argv)
    try:
        job = json.loads(args.job.read_text(encoding="utf-8-sig"))
        if job.get("duplicate_of"):
            raise ValueError(f"该岗位是重复记录，主记录为 {job['duplicate_of']}，拒绝重复生成材料")
        target = create_application_workspace(root, job, args.force_level)
        print(f"已创建草稿工作区: {target}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
