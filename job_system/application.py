from __future__ import annotations

import json
from pathlib import Path

from .common import APPLICATION_STATUSES, iso_today, sanitize_windows_name, write_json, write_text

BASE_FILES = (
    "job-description.md", "job-metadata.json", "company-research.md", "match-analysis.md",
    "application-strategy.md", "fact-check.md", "source-traceability.md", "status.md", "changelog.md",
)
FULL_FILES = (
    "cv-change-plan.md", "cv-de.md", "cv-en.md", "cover-letter-de.md", "cover-letter-en.md",
    "application-email-de.md", "application-email-en.md", "interview-prep.md",
)


def workspace_path(root: Path, job: dict) -> Path:
    return root / "applications" / sanitize_windows_name(job.get("company", "unknown-company")) / sanitize_windows_name(job.get("title", "unknown-role"))


def create_application_workspace(root: Path, job: dict, force_level: str | None = None) -> Path:
    if job.get("duplicate_of"):
        raise ValueError(f"重复岗位不得创建申请材料；主记录为 {job['duplicate_of']}")
    target = workspace_path(root, job)
    if target.exists():
        raise FileExistsError(f"申请工作区已存在，拒绝重复创建: {target}")
    grade = str(force_level or job.get("match_grade") or "C").upper()
    target.mkdir(parents=True, exist_ok=False)
    files = list(BASE_FILES) + (list(FULL_FILES) if grade in {"A", "B"} else [])
    if grade in {"D", "E"} and force_level is None:
        files = ["job-description.md", "job-metadata.json", "match-analysis.md", "status.md", "changelog.md"]
    for name in files:
        if name == "job-metadata.json":
            write_json(target / name, job)
        elif name == "job-description.md":
            write_text(target / name, f"# {job.get('title', '岗位说明')}\n\n来源：{job.get('source_url', 'NEEDS_CONFIRMATION')}\n\n{job.get('description', 'NEEDS_CONFIRMATION')}\n")
        elif name == "status.md":
            write_text(target / name, f"# 申请状态\n\n- status: preparing\n- last_updated: {iso_today()}\n- final_submission: USER_ONLY\n")
        elif name == "fact-check.md":
            write_text(target / name, "# 事实核查\n\n| Claim | Status | Source | Notes |\n|---|---|---|---|\n| NEEDS_CONFIRMATION | NEEDS_CONFIRMATION | | 初始化占位，不得进入正式材料 |\n")
        elif name == "source-traceability.md":
            write_text(target / name, "# 来源追踪\n\n| Material | Claim | Source document | Status |\n|---|---|---|---|\n")
        elif name == "changelog.md":
            write_text(target / name, f"# Changelog\n\n- {iso_today()}: 创建草稿工作区；未发送、未上传、未投递。\n")
        elif name == "cv-change-plan.md":
            write_text(target / name, "# CV Change Plan\n\n| Section | Original Text | Proposed Text | Reason | Related Job Requirement | Source Evidence | Fact Risk | Requires Confirmation | Approved |\n|---|---|---|---|---|---|---|---|---|\n")
        else:
            write_text(target / name, f"# {name.removesuffix('.md').replace('-', ' ').title()}\n\nDRAFT — 仅供人工审核。\n")
    return target


def update_status(status_file: Path, new_status: str, *, user_approved: bool = False) -> None:
    if new_status not in APPLICATION_STATUSES:
        raise ValueError(f"无效申请状态: {new_status}")
    if new_status == "approved" and not user_approved:
        raise PermissionError("标记 approved 需要用户明确批准")
    existing = status_file.read_text(encoding="utf-8") if status_file.exists() else "# 申请状态\n"
    lines = [line for line in existing.splitlines() if not line.startswith("- status:") and not line.startswith("- last_updated:")]
    lines.extend([f"- status: {new_status}", f"- last_updated: {iso_today()}", "- final_submission: USER_ONLY"])
    write_text(status_file, "\n".join(lines).rstrip() + "\n", overwrite=True)
