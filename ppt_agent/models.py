from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Brief:
    topic: str
    audience: str = "通用商业受众"
    slide_count: int = 8
    style: str = "consulting"
    source_text: str = ""


@dataclass
class Slide:
    index: int
    kind: str
    intent: str
    title: str
    bullets: list[str] = field(default_factory=list)
    speaker_notes: str = ""
    visual: str = ""
    layout: str = "title_and_content"


@dataclass
class Deck:
    title: str
    audience: str
    style: str
    theme: dict[str, str]
    slides: list[Slide]
    review_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
