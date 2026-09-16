#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.common import write_text
from job_system.reports import application_tracker_markdown, dashboard_markdown, read_jobs, top_opportunities_markdown, weekly_review_markdown


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="从本地岗位记录生成排名与周报")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="周报日期 YYYY-MM-DD")
    args = parser.parse_args(argv)
    try:
        jobs = read_jobs(root / "data/jobs")
        tracker_path = root / "data/applications/application-tracker.csv"
        with tracker_path.open("r", encoding="utf-8-sig", newline="") as handle:
            applications = list(csv.DictReader(handle))
        write_text(root / "reports/top-opportunities.md", top_opportunities_markdown(jobs, args.date), overwrite=True)
        write_text(root / "reports/job-search-dashboard.md", dashboard_markdown(jobs, applications, args.date), overwrite=True)
        write_text(root / "reports/application-tracker.md", application_tracker_markdown(applications), overwrite=True)
        output = root / "reports" / f"weekly-review-{args.date.isoformat()}.md"
        write_text(output, weekly_review_markdown(jobs, args.date), overwrite=output.exists())
        print(f"已生成 {output}、dashboard、tracker 和 top-opportunities")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
