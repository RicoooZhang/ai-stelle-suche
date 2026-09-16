from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import unicodedata
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

APPLICATION_STATUSES = (
    "discovered", "reviewing", "recommended", "skip", "preparing",
    "ready_for_review", "approved", "applied", "interview", "rejected",
    "withdrawn", "offer", "archived",
)
FACT_STATUSES = (
    "VERIFIED", "PARTIALLY_VERIFIED", "NEEDS_CONFIRMATION", "CONFLICTING",
    "NOT_SUPPORTED", "DO_NOT_USE",
)
SAMPLE_MARKER = "SAMPLE_DATA_NOT_REAL"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def iso_today() -> str:
    override = os.environ.get("AI_JOB_TODAY", "").strip()
    if override:
        try:
            return date.fromisoformat(override).isoformat()
        except ValueError as exc:
            raise ValueError("AI_JOB_TODAY 必须是 YYYY-MM-DD") from exc
    return date.today().isoformat()


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def normalize_url(value: str) -> str:
    if not value:
        return ""
    parts = urlsplit(value.strip())
    ignored = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "trk", "trackingid"}
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.casefold() not in ignored]
    query.sort()
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), parts.path.rstrip("/"), urlencode(query), ""))


def description_hash(value: str) -> str:
    normalized = normalize_text(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16] if normalized else ""


def job_fingerprint(job: dict) -> str:
    parts = [
        normalize_text(job.get("company")), normalize_text(job.get("title")),
        normalize_text(job.get("location")), normalize_url(str(job.get("source_url") or "")),
        normalize_text(job.get("source_job_id")),
        description_hash(str(job.get("description") or job.get("responsibilities") or "")),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]


def sanitize_windows_name(value: str, fallback: str = "unnamed") -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", str(value or ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if not cleaned:
        cleaned = fallback
    if cleaned.upper() in reserved:
        cleaned = f"_{cleaned}"
    return cleaned[:100].rstrip(" .") or fallback


def load_json(path: Path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"文件不存在: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败 {path}: 第 {exc.lineno} 行第 {exc.colno} 列: {exc.msg}") from exc


def load_json_yaml(path: Path) -> dict:
    """Load JSON-compatible YAML without a third-party YAML dependency."""
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"配置顶层必须是对象: {path}")
    return data


def backup_existing(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, backup)
    return backup


def write_text(path: Path, content: str, *, overwrite: bool = False, backup: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"拒绝覆盖已有文件: {path}")
    if path.exists() and backup:
        backup_existing(path)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def write_json(path: Path, data, *, overwrite: bool = False, backup: bool = True) -> Path:
    return write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n", overwrite=overwrite, backup=backup)
