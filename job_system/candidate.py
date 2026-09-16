from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from .common import iso_today, write_json

TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv"}
UNSUPPORTED_BINARY = {".pdf", ".doc", ".docx", ".odt", ".rtf", ".xlsx", ".xls"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_local_document(path: Path) -> dict:
    suffix = path.suffix.casefold()
    result = {
        "source_file": path.name, "sha256": file_sha256(path), "extracted_on": iso_today(),
        "status": "NEEDS_CONFIRMATION", "facts": [], "warnings": [],
    }
    if suffix in TEXT_EXTENSIONS:
        text = path.read_text(encoding="utf-8-sig")
        result["raw_text"] = text
        result["warnings"].append("文本已本地读取；尚未由人工逐项确认，不能进入正式材料。")
        return result
    if suffix in UNSUPPORTED_BINARY:
        result["warnings"].append(f"当前标准库实现不能可靠解析 {suffix}；请在 Codex 中使用对应文档/PDF能力人工审查，原文件未修改也未上传。")
        result["status"] = "EXTRACTION_NOT_AVAILABLE"
        return result
    result["warnings"].append(f"不支持的文件格式: {suffix or '(无扩展名)'}")
    result["status"] = "UNSUPPORTED_FORMAT"
    return result


def import_documents(source_dir: Path, extracted_dir: Path) -> list[dict]:
    source_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in source_dir.iterdir() if p.is_file() and p.name != ".gitkeep")
    results = []
    for path in files:
        result = extract_local_document(path)
        output = extracted_dir / f"{path.stem}.extracted.json"
        if output.exists():
            existing = json.loads(output.read_text(encoding="utf-8-sig"))
            if existing.get("sha256") == result["sha256"]:
                result["warnings"].append("相同文件此前已导入；未重复写入。")
                results.append(result)
                continue
        write_json(output, result, overwrite=output.exists())
        results.append(result)
    return results
