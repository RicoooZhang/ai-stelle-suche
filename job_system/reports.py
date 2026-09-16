from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from .common import SAMPLE_MARKER, iso_today, write_text


def read_jobs(directory: Path) -> list[dict]:
    jobs = []
    if not directory.exists():
        return jobs
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"无法读取岗位记录 {path}: {exc}") from exc
        if data.get("sample_marker") == SAMPLE_MARKER:
            continue
        jobs.append(data)
    return jobs


def write_csv_bom(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            normalized = {key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value for key, value in row.items()}
            writer.writerow(normalized)


def top_opportunities_markdown(jobs: list[dict], as_of: date | None = None) -> str:
    unique = [j for j in jobs if not j.get("duplicate_of")]
    unique.sort(key=lambda j: float(j.get("match_score") or 0), reverse=True)
    lines = ["# Top Opportunities", "", f"更新时间：{(as_of or date.today()).isoformat()}", "", "| 排名 | 公司 | 岗位 | 地点 | 远程 | 分数 | 等级 | 最大优势 | 主要差距 | 推荐行动 | 来源 | 发布日期 | 状态 |", "|---:|---|---|---|---|---:|---|---|---|---|---|---|---|"]
    for rank, job in enumerate(unique, start=1):
        strength = (job.get("strengths") or [""])[0] if isinstance(job.get("strengths"), list) else job.get("strengths", "")
        gap = (job.get("gaps") or [""])[0] if isinstance(job.get("gaps"), list) else job.get("gaps", "")
        lines.append(f"| {rank} | {job.get('company','')} | {job.get('title','')} | {job.get('location','')} | {job.get('remote_type','')} | {job.get('match_score','')} | {job.get('match_grade','')} | {strength} | {gap} | {job.get('recommended_action','')} | {job.get('source','')} | {job.get('date_posted','')} | {job.get('application_status','')} |")
    if not unique:
        lines.append("| - | 暂无真实岗位 | | | | | | | | | | | |")
    return "\n".join(lines) + "\n"


def dashboard_markdown(jobs: list[dict], applications: list[dict], as_of: date | None = None) -> str:
    unique = [j for j in jobs if not j.get("duplicate_of")]
    statuses = Counter(str(a.get("status") or "") for a in applications)
    grades = Counter(str(j.get("match_grade") or "") for j in unique)
    return "\n".join([
        "# Job Search Dashboard", "", f"更新时间：{(as_of or date.today()).isoformat()}", "",
        f"- 真实岗位记录：{len(jobs)}", f"- 去重后岗位：{len(unique)}",
        f"- A/B/C：{grades['A']} / {grades['B']} / {grades['C']}",
        f"- ready_for_review：{statuses['ready_for_review']}", f"- applied：{statuses['applied']}",
        f"- interview：{statuses['interview']}", f"- rejected：{statuses['rejected']}", "",
        "运行 `python scripts/generate_reports.py --date YYYY-MM-DD` 刷新。", "",
    ])


def application_tracker_markdown(applications: list[dict]) -> str:
    lines = [
        "# Application Tracker", "", "> 不保存护照号、身份证号、完整签证内容或其他不必要的敏感信息。系统不会发送消息或自动投递。", "",
        "| 公司 | 岗位 | 来源 | URL | 发现日期 | 截止日期 | 匹配分 | 语言 | 材料版本 | 状态 | 投递日期 | 联系人 | 面试日期 | 跟进日期 | 反馈 | 拒绝原因 | 下一步 | 更新时间 |",
        "|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in applications:
        values = [row.get(k, "") for k in ("company","title","source","source_url","date_found","deadline","match_score","application_language","materials_version","status","date_applied","contact_name","interview_date","follow_up_date","feedback","rejection_reason","next_action","last_updated")]
        lines.append("| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in values) + " |")
    return "\n".join(lines) + "\n"


def weekly_review_markdown(jobs: list[dict], as_of: date | None = None) -> str:
    as_of = as_of or date.today()
    start = as_of - timedelta(days=6)
    weekly = [j for j in jobs if start.isoformat() <= str(j.get("date_found", "")) <= as_of.isoformat()]
    unique = [j for j in weekly if not j.get("duplicate_of")]
    grades = Counter(j.get("match_grade") for j in unique)
    statuses = Counter(j.get("application_status") for j in jobs)
    top = sorted(unique, key=lambda j: float(j.get("match_score") or 0), reverse=True)[:5]
    gaps = Counter(g for j in unique for g in (j.get("gaps") or []) if isinstance(g, str))
    lines = [
        f"# Weekly Job Review — {as_of.isoformat()}", "", f"统计周期：{start.isoformat()} 至 {as_of.isoformat()}", "",
        f"- 本周新发现岗位数：{len(weekly)}", f"- 去重后岗位数：{len(unique)}",
        f"- A级岗位：{grades['A']}", f"- B级岗位：{grades['B']}", f"- C级岗位：{grades['C']}",
        f"- 已准备材料岗位：{statuses['ready_for_review'] + statuses['preparing']}", f"- 已投递岗位：{statuses['applied']}",
        f"- 面试岗位：{statuses['interview']}", f"- 被拒岗位：{statuses['rejected']}", "", "## 最值得申请的5个岗位", "",
    ]
    lines.extend([f"{idx}. {j.get('company')} — {j.get('title')}（{j.get('match_score')}/{j.get('match_grade')}）" for idx, j in enumerate(top, 1)] or ["暂无。"])
    lines.extend(["", "## 最常见技能差距", ""])
    lines.extend([f"- {gap}: {count}" for gap, count in gaps.most_common(10)] or ["- 暂无足够数据。"])
    lines.extend(["", "## 最匹配的岗位类别", "", "NEEDS_CONFIRMATION：数据积累后按 normalized_title 汇总。", "", "## 下一周建议行动", "", "1. 人工审核 A/B 岗位及事实来源。", "2. 补齐最高频、真实可弥补的技能差距。", "3. 由用户本人完成已批准岗位的最终投递。", ""])
    return "\n".join(lines)
