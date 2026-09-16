---
name: search-germany-jobs
description: Search and organize Germany ERP, application support, digitalization, IT process, and related jobs. Use for weekly searches, NRW or Köln-area searches, remote/hybrid searches, and Chinese-company-in-Germany searches.
---

# Search Germany jobs

1. Read `config/targets.json` and `config/job-sources.yaml`.
2. Generate German and English queries for the requested role/location/time window.
3. Use only public access explicitly permitted by the source. Stop at login, CAPTCHA, consent, robots/terms uncertainty, or access denial; give the user queries and request pasted URLs/text.
4. Record source, source URL, discovery date, posting date when verified, and access limitations.
5. Normalize each job with `scripts/analyze_job.py`; do not infer missing facts.
6. Run `scripts/deduplicate_jobs.py --write`, preserving every source URL and one master record.
7. Score against verified candidate evidence and sort A–E. Penalize infeasible distant on-site roles and identify pure development/sales roles.
8. Save a search log under `data/searches/` and update reports.

Do not log in, bypass controls, upload documents, or apply.
