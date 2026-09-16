---
name: job-task
description: Start and route a guided task in this Germany job-search project. Use when the user invokes $job-task, asks to start a job-search task without knowing which project skill to use, or wants Codex to collect missing task details one question at a time before selecting the correct workflow.
---

# Start a job task

Act as the single intake and routing entry point for this project. Collect only information that materially affects the requested outcome, then hand the task to the appropriate project skill.

## Intake

1. Read the user's current message and retain every detail already supplied. Never ask for information that is already available in the conversation or project files.
2. Identify the intended outcome. If it is unclear, ask what the user wants to accomplish.
3. Ask at most one concise question per response. Ask the highest-impact missing question first and continue across turns until the task can be routed safely.
4. Prefer a proposed default when a low-impact choice is missing. Do not ask for optional details that the downstream skill can determine from project evidence.
5. Request only the minimum applicable inputs:
   - target outcome or workflow;
   - job URL, pasted job text, saved job/application reference, company name, or candidate document path;
   - requested language when it cannot be inferred;
   - scope, time window, location, or output format when it materially changes the work;
   - protected content or constraints beyond the repository rules.
6. Do not browse, edit files, generate application artifacts, or take external actions while material intake information is still missing.

## Routing

Select the smallest workflow that satisfies the request:

| User outcome | Route to |
| --- | --- |
| Import or reconcile CVs, certificates, references, or candidate facts | `$import-candidate-documents` |
| Find Germany-based jobs | `$search-germany-jobs` |
| Normalize, save, score, compare, or assess a vacancy | `$analyze-job` |
| Research an employer | `$research-company` |
| Assemble a complete review-only application workspace/package | `$generate-application-package` |
| Tailor a German or English CV | `$tailor-cv` |
| Draft a cover letter | `$write-cover-letter` |
| Export preview or approved application documents | `$export-application-documents` |
| Prepare for an interview | `$prepare-interview` |
| Record an application event or status change | `$track-application` |
| Produce weekly counts, rankings, gap patterns, or next actions | `$weekly-job-review` |

For a request that genuinely requires several workflows, state the dependency order and begin with the first unmet prerequisite. Do not run multiple overlapping workflows merely because they are available.

## Handoff

Once the minimum information is complete:

1. Summarize the understood goal, supplied input, selected route, language, requested deliverable, and important constraints in a compact task brief.
2. State which project skill will be used and why.
3. Follow the repository Requirement Gate. For a build, change, design, export, or artifact-creation request, provide an `实施确认单` and wait for the user to reply `批准实施` or `开始实现`. For a simple question, explanation, read-only review, status check, or analysis-only outcome, proceed without creating an unnecessary approval gate.
4. After any required approval, invoke and follow the selected downstream skill completely. Do not replace its fact checks, prerequisites, validation, or safety rules with this intake workflow.

## Safety

- Use only source-supported candidate facts. Mark unresolved facts `NEEDS_CONFIRMATION` and never resolve conflicts silently.
- Never apply, submit, send, upload, register, log in, bypass access controls, or click a final submission step.
- Keep generated application materials in review status unless the repository rules and explicit user approval allow a status change.
- If the user asks for prohibited submission activity, explain the manual boundary and route only the safe preparation portion.
