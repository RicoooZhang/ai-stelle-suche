from __future__ import annotations

from difflib import SequenceMatcher

from .common import job_fingerprint, normalize_text, normalize_url


def duplicate_score(left: dict, right: dict) -> float:
    if normalize_url(str(left.get("source_url") or "")) and normalize_url(str(left.get("source_url") or "")) == normalize_url(str(right.get("source_url") or "")):
        return 1.0
    if left.get("source_job_id") and left.get("source_job_id") == right.get("source_job_id") and normalize_text(left.get("company")) == normalize_text(right.get("company")):
        return 1.0
    company = SequenceMatcher(None, normalize_text(left.get("company")), normalize_text(right.get("company"))).ratio()
    title = SequenceMatcher(None, normalize_text(left.get("title")), normalize_text(right.get("title"))).ratio()
    location = SequenceMatcher(None, normalize_text(left.get("location")), normalize_text(right.get("location"))).ratio()
    desc_left = normalize_text(left.get("description") or left.get("responsibilities"))[:4000]
    desc_right = normalize_text(right.get("description") or right.get("responsibilities"))[:4000]
    description = SequenceMatcher(None, desc_left, desc_right).ratio() if desc_left and desc_right else 0
    return round(company * 0.3 + title * 0.3 + location * 0.1 + description * 0.3, 4)


def find_duplicates(jobs: list[dict], threshold: float = 0.84) -> list[dict]:
    records = []
    for job in jobs:
        current = dict(job)
        current.setdefault("fingerprint", job_fingerprint(current))
        current.setdefault("duplicate_of", "")
        for master in records:
            if duplicate_score(master, current) >= threshold:
                current["duplicate_of"] = master.get("job_id") or master["fingerprint"]
                urls = set(master.get("all_source_urls", []))
                if master.get("source_url"):
                    urls.add(master["source_url"])
                if current.get("source_url"):
                    urls.add(current["source_url"])
                master["all_source_urls"] = sorted(urls)
                break
        records.append(current)
    return records
