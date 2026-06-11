from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .models import Deck


class DeckExporter:
    def export_json(self, deck: Deck, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "deck.json"
        path.write_text(json.dumps(deck.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def export_markdown(self, deck: Deck, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        lines = [f"# {deck.title}", "", f"受众：{deck.audience}", f"风格：{deck.style}", ""]
        for slide in deck.slides:
            lines.extend([f"## {slide.index}. {slide.title}", "", f"意图：{slide.intent}", ""])
            lines.extend(f"- {bullet}" for bullet in slide.bullets)
            lines.extend(["", f"视觉建议：{slide.visual}", f"备注：{slide.speaker_notes}", ""])
        lines.extend(["## Review", ""])
        lines.extend(f"- {note}" for note in deck.review_notes)

        path = out_dir / "deck.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


class PptxRenderer:
    def render(self, deck: Deck, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        input_path = out_dir / "deck.json"
        path = out_dir / "deck.pptx"
        script_path = Path(__file__).resolve().parents[1] / "scripts" / "render_deck.cjs"
        if not script_path.exists():
            raise RuntimeError(f"缺少 PptxGenJS 渲染脚本：{script_path}")

        result = subprocess.run(
            ["node", str(script_path), str(input_path), str(path)],
            cwd=str(script_path.parents[1]),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"PptxGenJS 导出失败：{details}")
        if not path.exists():
            raise RuntimeError("PptxGenJS 未生成 deck.pptx。")
        return path
