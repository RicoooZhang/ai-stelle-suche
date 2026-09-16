from __future__ import annotations

import re
from datetime import date

from .common import job_fingerprint, normalize_text

JOB_FIELDS = (
    "job_id", "fingerprint", "title", "normalized_title", "company", "normalized_company",
    "location", "distance_relevance", "remote_type", "source", "source_url", "date_found",
    "date_posted", "date_expired", "language", "employment_type", "seniority", "salary",
    "salary_currency", "work_authorization_requirements", "visa_requirements", "required_skills",
    "preferred_skills", "required_experience", "responsibilities", "company_summary", "industry",
    "software_stack", "match_score", "match_grade", "hard_requirements_met",
    "hard_requirements_missing", "transferable_skills", "strengths", "gaps", "risks",
    "recommended_action", "application_language", "application_status", "duplicate_of", "notes",
    "last_updated",
)


def parse_job_text(text: str, *, source_url: str = "", source: str = "manual") -> dict:
    if len(text.strip()) < 40:
        raise ValueError("岗位正文过短；请提供完整招聘信息或结构化 JSON")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0][:200]
    company = "NEEDS_CONFIRMATION"
    location = "NEEDS_CONFIRMATION"
    for line in lines[:20]:
        match = re.match(r"(?i)(company|unternehmen|firma)\s*[:：-]\s*(.+)", line)
        if match:
            company = match.group(2).strip()
        match = re.match(r"(?i)(location|standort|ort)\s*[:：-]\s*(.+)", line)
        if match:
            location = match.group(2).strip()
    language = "de" if re.search(r"\b(aufgaben|anforderungen|wir bieten|bewerbung)\b", text.casefold()) else "en"
    remote_type = "remote" if re.search(r"\b(remote|homeoffice|home-office)\b", text.casefold()) else "NEEDS_CONFIRMATION"
    job = {field: "" for field in JOB_FIELDS}
    job.update({
        "title": title, "normalized_title": normalize_text(title), "company": company,
        "normalized_company": normalize_text(company), "location": location, "remote_type": remote_type,
        "source": source, "source_url": source_url, "date_found": date.today().isoformat(),
        "language": language, "responsibilities": text, "description": text,
        "required_skills": [], "preferred_skills": [], "hard_requirements_met": [],
        "hard_requirements_missing": [], "transferable_skills": [], "strengths": [], "gaps": [],
        "risks": ["自动提取有限，硬性要求/偏好需人工复核"], "application_language": language,
        "application_status": "discovered", "notes": "Imported locally; no application submitted.",
        "last_updated": date.today().isoformat(),
    })
    job["fingerprint"] = job_fingerprint(job)
    job["job_id"] = f"job-{job['fingerprint']}"
    return job


def validate_job_record(job: dict) -> list[str]:
    errors = []
    for field in ("title", "company", "location", "source", "date_found", "application_status"):
        if not job.get(field):
            errors.append(f"缺少必填字段: {field}")
    if job.get("application_status") not in {"discovered", "reviewing", "recommended", "skip", "preparing", "ready_for_review", "approved", "applied", "interview", "rejected", "withdrawn", "offer", "archived"}:
        errors.append(f"无效 application_status: {job.get('application_status')}")
    return errors
