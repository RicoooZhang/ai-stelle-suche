from __future__ import annotations

from pathlib import Path

from .common import load_json_yaml, project_root


def load_scoring_config(path: Path | None = None) -> dict:
    return load_json_yaml(path or project_root() / "config" / "scoring.yaml")


def grade_for(score: float, config: dict) -> str:
    for grade, limits in config["grades"].items():
        if limits["min"] <= score <= limits["max"]:
            return grade
    raise ValueError(f"分数超出 0-100: {score}")


def score_job(job: dict, config: dict | None = None) -> dict:
    config = config or load_scoring_config()
    ratings = job.get("dimension_ratings", {})
    if not isinstance(ratings, dict):
        raise ValueError("dimension_ratings 必须是对象，值为 0.0 到 1.0")
    details = {}
    total = 0.0
    for key, spec in config["dimensions"].items():
        rating = float(ratings.get(key, 0))
        if not 0 <= rating <= 1:
            raise ValueError(f"评分维度 {key} 必须在 0.0 到 1.0 之间")
        points = round(rating * float(spec["weight"]), 2)
        details[key] = {"label": spec["label"], "rating": rating, "points": points, "max": spec["weight"]}
        total += points

    vetoes = []
    penalties = 0.0
    flags = set(job.get("risk_flags", []))
    for rule in config.get("penalties", []):
        if rule["id"] in flags:
            penalties += float(rule.get("points", 0))
            if rule.get("veto"):
                vetoes.append(rule["id"])
    raw_total = round(total, 2)
    final_total = max(0.0, min(100.0, round(raw_total - penalties, 2)))
    grade = grade_for(final_total, config)
    recommendation = config["grades"][grade]["recommendation"]
    if vetoes:
        recommendation = "存在待人工核实的否决因素；在确认前不建议准备正式材料"
    strengths = job.get("strengths") or []
    gaps = job.get("gaps") or []
    should_apply = not vetoes and grade in {"A", "B", "C"}
    return {
        "match_score": final_total,
        "match_grade": grade,
        "score_before_penalties": raw_total,
        "penalty_points": penalties,
        "score_details": details,
        "veto_flags": vetoes,
        "recommended_action": recommendation,
        "biggest_strengths": strengths,
        "main_gaps": gaps,
        "hard_requirements": job.get("hard_requirements", []),
        "hard_requirements_met": job.get("hard_requirements_met", []),
        "hard_requirements_missing": job.get("hard_requirements_missing", []),
        "transferable_skills": job.get("transferable_skills", []),
        "risks": job.get("risks", []),
        "should_apply": should_apply,
        "application_language": job.get("application_language") or job.get("language") or "NEEDS_CONFIRMATION",
        "worth_tailoring_materials": grade in {"A", "B"},
        "gaps_improvable_by_expression": job.get("gaps_improvable_by_expression", []),
        "gaps_not_fixable_by_rewriting": job.get("gaps_not_fixable_by_rewriting", []),
        "needs_confirmation": job.get("needs_confirmation", []),
    }
