---
name: import-candidate-documents
description: Import local CVs, Arbeitszeugnisse, reference letters, and certificates into the Germany job-search fact profile. Use when the user adds files to candidate/source-documents or asks to initialize, refresh, reconcile, or source candidate facts.
---

# Import candidate documents

1. Read `AGENTS.md`, `candidate/profile/do-not-claim.md`, and the existing profile files.
2. Inventory `candidate/source-documents/`; never modify, rename, upload, or overwrite source files.
3. For deterministic text extraction run `python scripts/import_candidate_documents.py`. For PDF/DOCX use the available document/PDF reading capability locally and visually verify extraction; do not use external conversion services.
4. Extract atomic claims with file and page/section locations. Mark each `VERIFIED`, `PARTIALLY_VERIFIED`, `NEEDS_CONFIRMATION`, or `CONFLICTING`.
5. Update `source-index.md` first, then `profile-conflicts.md`, `verified-skills.md`, and finally `master-profile.md`. Back up changed files.
6. Keep uncertain information under Unverified/Missing Information. Never resolve conflicts or infer language level, dates, numbers, work authorization, or credentials.
7. Report files processed, unsupported formats, verified facts, conflicts, and user confirmations needed.

Do not create application materials during this workflow.
