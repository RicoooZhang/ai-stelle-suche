from __future__ import annotations

from .common import FACT_STATUSES

BLOCKED_FACT_STATUSES = {"NOT_SUPPORTED", "DO_NOT_USE", "CONFLICTING", "NEEDS_CONFIRMATION"}


def validate_fact_records(records: list[dict]) -> list[str]:
    errors = []
    for index, record in enumerate(records, start=1):
        status = record.get("status")
        if status not in FACT_STATUSES:
            errors.append(f"事实记录 {index} 使用无效状态: {status}")
        if not str(record.get("claim") or "").strip():
            errors.append(f"事实记录 {index} 缺少 claim")
        if status in {"VERIFIED", "PARTIALLY_VERIFIED"} and not record.get("source"):
            errors.append(f"事实记录 {index} 标记为 {status} 但缺少 source")
    return errors


def blocked_claims_in_material(material: str, records: list[dict]) -> list[dict]:
    material_folded = material.casefold()
    violations = []
    for record in records:
        claim = str(record.get("claim") or "").strip()
        if claim and record.get("status") in BLOCKED_FACT_STATUSES and claim.casefold() in material_folded:
            violations.append(record)
    for marker in ("NEEDS_CONFIRMATION", "NOT_SUPPORTED", "DO_NOT_USE"):
        if marker.casefold() in material_folded:
            violations.append({"claim": marker, "status": marker, "source": "material marker"})
    return violations
