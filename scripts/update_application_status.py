#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.application import update_status
from job_system.common import APPLICATION_STATUSES


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="更新本地申请状态；不联系招聘方")
    parser.add_argument("status_file", type=Path)
    parser.add_argument("status", choices=APPLICATION_STATUSES)
    parser.add_argument("--user-approved", action="store_true", help="仅在用户已明确批准时用于 approved 状态")
    args = parser.parse_args(argv)
    try:
        update_status(args.status_file, args.status, user_approved=args.user_approved)
        print(f"已更新为 {args.status}: {args.status_file}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
