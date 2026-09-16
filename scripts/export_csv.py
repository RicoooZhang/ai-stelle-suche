#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from job_system.reports import read_jobs, write_csv_bom

JOB_FIELDS = ["job_id","fingerprint","title","company","location","remote_type","source","source_url","date_found","date_posted","language","employment_type","seniority","match_score","match_grade","recommended_action","application_status","duplicate_of","last_updated"]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="导出 UTF-8 BOM CSV，便于 Windows Excel 打开")
    parser.add_argument("--kind", choices=("jobs", "applications", "companies", "all"), default="all")
    args = parser.parse_args(argv)
    try:
        if args.kind in {"jobs", "all"}:
            write_csv_bom(root / "data/exports/jobs.csv", read_jobs(root / "data/jobs"), JOB_FIELDS)
        if args.kind in {"applications", "all"}:
            rows = read_csv(root / "data/applications/application-tracker.csv")
            fields = list(rows[0]) if rows else ["application_id","company","title","source","source_url","date_found","deadline","match_score","application_language","materials_version","status","date_applied","contact_name","contact_method","interview_date","follow_up_date","feedback","rejection_reason","next_action","last_updated"]
            write_csv_bom(root / "data/exports/applications.csv", rows, fields)
        if args.kind in {"companies", "all"}:
            rows = []
            for path in sorted((root / "data/companies").glob("*.json")):
                import json
                rows.append(json.loads(path.read_text(encoding="utf-8-sig")))
            fields = list(rows[0]) if rows else ["company_id","company_name","official_name","website","headquarters","germany_locations","industry","products","services","company_size","ownership","german_entity","china_connection","international_presence","technology_environment","erp_environment","known_products","target_customers","company_culture_signals","hiring_focus","recent_relevant_information","sources","last_updated","confidence_level"]
            write_csv_bom(root / "data/exports/companies.csv", rows, fields)
        print("CSV 导出完成；未包含原始个人文件或证件数据。")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
