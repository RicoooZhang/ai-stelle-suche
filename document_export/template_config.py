from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_GERMAN_CV_TEMPLATE = "german-professional"
LEGACY_RESUME_TEMPLATE = "resume-legacy"


@dataclass(frozen=True)
class TemplateSelection:
    template_id: str
    name: str
    path: Path


def _registry(template_root: Path) -> dict:
    path = template_root / "resume" / "templates.json"
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_template(template_root: Path, document_type: str, language: str, requested: str = "") -> TemplateSelection:
    if document_type != "cv":
        path = template_root / "cover-letter"
        return TemplateSelection("cover-letter-default", "Cover Letter Default", path)

    registry = _registry(template_root)
    template_id = requested or registry.get("defaults", {}).get("cv", {}).get(language, LEGACY_RESUME_TEMPLATE)
    metadata = registry.get("templates", {}).get(template_id)
    if not metadata:
        raise ValueError(f"unknown resume template: {template_id}")
    if language not in metadata.get("languages", []):
        raise ValueError(f"template {template_id} does not support language {language}")
    if document_type not in metadata.get("document_types", []):
        raise ValueError(f"template {template_id} does not support document type {document_type}")
    return TemplateSelection(template_id, str(metadata.get("name") or template_id), template_root / str(metadata["path"]))
