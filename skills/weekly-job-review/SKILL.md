---
name: weekly-job-review
description: Generate a weekly local review of discovered, deduplicated, scored, prepared, applied, interview, rejected, and follow-up jobs. Use for weekly reports, dashboards, gap patterns, and top-opportunity lists.
---

# Weekly job review

1. Read saved real job records and the application tracker; exclude `SAMPLE_DATA_NOT_REAL` and duplicates from totals.
2. Run `python scripts/generate_reports.py` and `python scripts/export_csv.py`.
3. Verify counts for new, unique, A/B/C, prepared, applied, interview, and rejected records.
4. List the top five opportunities with evidence, most common real gaps, strongest role categories, and next-week actions.
5. Flag stale, expired, incomplete, or conflicting records; do not guess missing outcomes.
6. Save `reports/weekly-review-YYYY-MM-DD.md` and update dashboard/top opportunities.

Reporting only; do not contact recruiters.
