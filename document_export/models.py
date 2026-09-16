from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class InlineRun:
    text: str
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True)
class Block:
    kind: str
    level: int = 0
    runs: tuple[InlineRun, ...] = ()

    @property
    def text(self) -> str:
        return "".join(run.text for run in self.runs)


@dataclass
class StructuredDocument:
    source: Path
    document_type: str
    language: str
    title: str = ""
    contact_line: str = ""
    blocks: list[Block] = field(default_factory=list)
    draft_markers_removed: int = 0

    def plain_text(self) -> str:
        return "\n".join(block.text for block in self.blocks if block.text)


@dataclass
class ValidationResult:
    passed: bool
    checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

