---
name: tailor-cv
description: Tailor a German or English CV for a specific analyzed job using only source-verified candidate facts. Use after job analysis and strategy when the user asks for a CV change plan or candidate CV draft.
---

# Tailor a CV

1. Require a saved job analysis, application strategy, master profile, source index, and fact statuses.
2. Choose German for German-local roles and English for international/English roles unless the user directs otherwise.
3. Create `cv-change-plan.md` before editing: prioritize relevant verified items, reorder sections, reduce irrelevant detail, and list keywords genuinely supported.
4. Preserve chronology, employers, titles, dates, degrees, certificates, software names, language levels, and numbers exactly as sourced.
5. Write a candidate version to `cv-de.md` or `cv-en.md`; never modify an original CV.
6. Add every claim to `source-traceability.md`, run `scripts/validate_application_facts.py`, and record changes in `changelog.md`.
7. Leave unsupported gaps visible; wording cannot fix a real capability gap.

Output is a draft and must remain `ready_for_review`; never upload it.
