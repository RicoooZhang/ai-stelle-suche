---
name: generate-application-package
description: Assemble a review-only application package from a saved job analysis, company research, strategy, CV plan/draft, cover letter, and fact traceability. Use for A/B jobs by default or any job when the user explicitly requests a package.
---

# Generate an application package

1. Reject duplicate jobs and require a saved normalized record. A/B may receive full materials; C receives strategy first; D/E require explicit user direction.
2. Run `python scripts/create_application_workspace.py <job.json>` to create a non-overwriting workspace.
3. Complete company research, match analysis, strategy, CV change plan, selected-language CV/letter, interview preparation, fact check, and traceability in that order.
4. Generate only files needed for the role; do not create empty claims to fill every template.
5. Run fact validation and review every number, date, skill, software, language, certificate, education, authorization, project, responsibility, and result.
6. Set status to `ready_for_review`, never automatically to `approved` or `applied`.
7. Summarize missing confirmations and manual submission steps.
8. After content generation and fact validation, invoke `export-application-documents` only when the user requests exported files. Default to preview for `ready_for_review`; do not generate unmarked final files before explicit approval.

Never send, upload, log in, or make the final submission.
