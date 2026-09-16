---
name: track-application
description: Update local job-application status, dates, contacts, interviews, feedback, and next actions while preventing duplicate applications. Use when the user reports an application event or asks to update the tracker.
---

# Track an application

1. Identify the master job by fingerprint and confirm it is not a duplicate source.
2. Accept only statuses defined in `job_system.common.APPLICATION_STATUSES`.
3. Require explicit user approval for `approved`; a report that the user applied may set `applied` and date without sending anything.
4. Run `python scripts/update_application_status.py <status.md> <status>` and update `data/applications/application-tracker.csv` plus `reports/application-tracker.md`.
5. Record company, role, source, URL, dates, score, language, material version, minimal contact details, feedback, next action, and last update.
6. Never store passport/identity numbers, complete visa contents, passwords, cookies, or unrelated sensitive data.
7. Back up tracker files and report every changed path.

Never send follow-ups, emails, messages, uploads, or applications.
