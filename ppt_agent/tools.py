from __future__ import annotations

import json
import subprocess
import shutil
from pathlib import Path
from typing import Any

from .llm import LLMClient, LLMError


def _get_llm_client() -> LLMClient | None:
    """懒加载 LLMClient，失败返回 None。"""
    try:
        return LLMClient()
    except (LLMError, Exception):
        return None


def _execute_with_mode(mode: str, rule_fn, llm_fn):
    """统一的双模式执行逻辑。返回 (结果, 实际使用的模式)。"""
    if mode == "rule":
        return rule_fn(), "rule"

    if mode == "llm":
        try:
            return llm_fn(), "llm"
        except (LLMError, Exception):
            return rule_fn(), "rule_fallback"

    # mode == "auto"
    client = _get_llm_client()
    if client is None:
        return rule_fn(), "rule"
    try:
        return llm_fn(client), "llm"
    except (LLMError, Exception):
        return rule_fn(), "rule_fallback"


def create_brief(
    topic: str,
    audience: str = "通用商业受众",
    slide_count: int = 8,
    style: str = "consulting",
    source_text: str = "",
) -> dict[str, Any]:
    """根据用户输入创建Brief对象，返回JSON格式的Brief。"""
    slide_count = max(3, min(slide_count, 30))
    brief = {
        "topic": topic.strip(),
        "audience": audience.strip() or "通用商业受众",
        "slide_count": slide_count,
        "style": style.strip() or "consulting",
        "source_text": source_text.strip(),
    }
    _write_json("/workspace/brief.json", brief)
    return brief


def extract_insights(brief_json: str, mode: str = "rule") -> list[str]:
    """从Brief的资料中提取关键洞察。支持 rule/llm/auto 模式。"""
    brief = json.loads(brief_json) if isinstance(brief_json, str) else brief_json

    def rule():
        if not brief.get("source_text"):
            return [
                f"{brief['topic']} 的价值需要围绕受众关心的问题展开。",
                "好的商业演示应先建立背景，再提出判断，最后给出行动建议。",
                "页面应控制信息密度，让每页只有一个清晰意图。",
            ]
        lines = [line.strip("- ").strip() for line in brief["source_text"].splitlines()]
        result = [line for line in lines if len(line) >= 8]
        return result[:8] or [brief["source_text"][:120]]

    def llm(client: LLMClient):
        return client.extract_insights_from_text(
            brief["topic"], brief.get("source_text", ""), brief["audience"]
        )

    insights, mode_used = _execute_with_mode(mode, rule, llm)

    if not insights:
        insights = rule()

    _write_json("/workspace/insights.json", insights)
    return insights


def build_outline(brief_json: str, insights_json: str, mode: str = "rule") -> list[dict[str, str]]:
    """构建PPT叙事大纲。支持 rule/llm/auto 模式。"""
    brief = json.loads(brief_json) if isinstance(brief_json, str) else brief_json
    insights = json.loads(insights_json) if isinstance(insights_json, str) else insights_json
    slide_count = brief["slide_count"]

    def rule():
        base = [
            ("title", "建立主题和汇报对象的期待"),
            ("context", "解释为什么现在需要关注这个问题"),
            ("problem", "定义现有痛点和机会缺口"),
            ("insight", "给出核心判断和关键洞察"),
            ("framework", "用结构化框架解释方案"),
            ("evidence", "展示数据、案例或趋势证据"),
            ("roadmap", "说明落地路径和优先级"),
            ("closing", "总结价值并提出下一步行动"),
        ]

        if slide_count <= len(base):
            selected = base[:slide_count]
        else:
            selected = base[:-1]
            extra_count = slide_count - len(base)
            selected.extend(("deep_dive", f"展开关键议题 {i + 1}") for i in range(extra_count))
            selected.append(base[-1])

        return [{"kind": kind, "intent": intent} for kind, intent in selected]

    def llm(client: LLMClient):
        return client.build_outline_for_topic(
            brief["topic"], brief["audience"], slide_count, brief["style"], insights
        )

    outline, mode_used = _execute_with_mode(mode, rule, llm)

    _write_json("/workspace/outline.json", outline)
    return outline


def write_slides(
    brief_json: str,
    outline_json: str,
    insights_json: str,
    mode: str = "rule",
) -> list[dict[str, Any]]:
    """为每页生成标题、要点、演讲备注和视觉建议。支持 rule/llm/auto 模式。"""
    brief = json.loads(brief_json) if isinstance(brief_json, str) else brief_json
    outline = json.loads(outline_json) if isinstance(outline_json, str) else outline_json
    insights = json.loads(insights_json) if isinstance(insights_json, str) else insights_json

    def rule():
        slides = []
        for idx, item in enumerate(outline, start=1):
            kind = item["kind"]
            slides.append({
                "index": idx,
                "kind": kind,
                "intent": item["intent"],
                "title": _title_for(kind, brief["topic"]),
                "bullets": _bullets_for(kind, brief, insights),
                "speaker_notes": f"本页重点：{item['intent']}。面向{brief['audience']}，讲清楚它与{brief['topic']}的关系。",
                "visual": _visual_for(kind),
            })
        return slides

    def llm(client: LLMClient):
        plan = client.create_deck_plan(
            topic=brief["topic"],
            audience=brief["audience"],
            slide_count=brief["slide_count"],
            style=brief["style"],
            outline=outline,
            insights=insights,
            source_text=brief.get("source_text", ""),
        )
        slides = plan.get("slides", [])
        for idx, slide in enumerate(slides, start=1):
            slide["index"] = idx
            slide.setdefault("layout", "title_and_content")
        return slides

    slides, mode_used = _execute_with_mode(mode, rule, llm)

    _write_json("/workspace/slides.json", slides)
    return slides


def apply_design(
    brief_json: str,
    slides_json: str,
    visual_style: str = "dark-premium",
) -> dict[str, Any]:
    """应用视觉主题和布局，生成完整Deck。"""
    brief = json.loads(brief_json) if isinstance(brief_json, str) else brief_json
    slides_data = json.loads(slides_json) if isinstance(slides_json, str) else slides_json

    themes = {
        "dark-premium": {
            "primary": "0A0A0A",
            "secondary": "1D1D1F",
            "accent": "00D4FF",
            "background": "0A0A0A",
            "surface": "141414",
            "text": "FFFFFF",
            "muted": "A1A1AA",
            "headerFont": "Arial Black",
            "bodyFont": "Arial",
        },
        "glassmorphism": {
            "primary": "667EEA",
            "secondary": "00D4FF",
            "accent": "F093FB",
            "background": "111827",
            "surface": "FFFFFF",
            "text": "FFFFFF",
            "muted": "DBEAFE",
            "headerFont": "Trebuchet MS",
            "bodyFont": "Calibri",
        },
        "gradient-modern": {
            "primary": "7C3AED",
            "secondary": "EC4899",
            "accent": "F97316",
            "background": "111827",
            "surface": "FFFFFF",
            "text": "FFFFFF",
            "muted": "E5E7EB",
            "headerFont": "Trebuchet MS",
            "bodyFont": "Calibri",
        },
        "keynote": {
            "primary": "000000",
            "secondary": "1D1D1F",
            "accent": "0071E3",
            "background": "000000",
            "surface": "111111",
            "text": "FFFFFF",
            "muted": "BFC3C9",
            "headerFont": "Arial Black",
            "bodyFont": "Arial",
        },
        "minimal-swiss": {
            "primary": "000000",
            "secondary": "F5F5F0",
            "accent": "FF0000",
            "background": "FAFAF9",
            "surface": "FFFFFF",
            "text": "000000",
            "muted": "525252",
            "headerFont": "Arial",
            "bodyFont": "Arial",
        },
        "editorial": {
            "primary": "2D2D2D",
            "secondary": "F5F5F0",
            "accent": "7C2D12",
            "background": "F5F5F0",
            "surface": "FFFFFF",
            "text": "2D2D2D",
            "muted": "6B625A",
            "headerFont": "Georgia",
            "bodyFont": "Calibri",
        },
        "3d-isometric": {
            "primary": "8B5CF6",
            "secondary": "EDE9FE",
            "accent": "14B8A6",
            "background": "FAFAFA",
            "surface": "FFFFFF",
            "text": "1F2937",
            "muted": "64748B",
            "headerFont": "Trebuchet MS",
            "bodyFont": "Calibri",
        },
    }

    theme = dict(themes.get(visual_style, themes["dark-premium"]))
    theme["deerStyle"] = visual_style

    for slide in slides_data:
        if slide["kind"] == "title":
            slide["layout"] = "title"
        elif slide["kind"] in {"framework", "roadmap"}:
            slide["layout"] = "diagram"
        else:
            slide["layout"] = "title_and_content"

    deck = {
        "title": brief["topic"],
        "audience": brief["audience"],
        "style": brief["style"],
        "theme": theme,
        "slides": slides_data,
        "review_notes": [],
    }

    _write_json("/workspace/deck.json", deck)
    return deck


def review_deck(deck_json: str, mode: str = "rule") -> dict[str, Any]:
    """检查Deck质量并返回审查意见。支持 rule/llm/auto 模式。"""
    deck = json.loads(deck_json) if isinstance(deck_json, str) else deck_json

    def rule():
        notes = []
        for slide in deck.get("slides", []):
            if not slide.get("title"):
                notes.append(f"第 {slide['index']} 页缺少标题。")
            if len(slide.get("bullets", [])) > 5:
                notes.append(f"第 {slide['index']} 页要点过多，建议压缩到 5 条以内。")
            if any(len(b) > 42 for b in slide.get("bullets", [])):
                notes.append(f"第 {slide['index']} 页存在较长 bullet，建议拆分或改写。")
        return notes or ["基础检查通过：标题、页数和页面密度正常。"]

    def llm(client: LLMClient):
        rule_notes = rule()
        llm_notes = client.review_deck_quality(json.dumps(deck, ensure_ascii=False))
        return rule_notes + llm_notes

    notes, mode_used = _execute_with_mode(mode, rule, llm)

    deck["review_notes"] = notes
    _write_json("/workspace/deck.json", deck)
    return deck


def generate_html_preview(deck_json: str, mode: str = "rule") -> str:
    """生成HTML预览页面。"""
    deck = json.loads(deck_json) if isinstance(deck_json, str) else deck_json

    theme = deck.get("theme", {})
    slides = deck.get("slides", [])

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{deck.get('title', 'PPT预览')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: {theme.get('bodyFont', 'Arial')}, sans-serif;
            background: #{theme.get('background', '0A0A0A')};
            color: #{theme.get('text', 'FFFFFF')};
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-family: {theme.get('headerFont', 'Arial Black')}, sans-serif;
            font-size: 2.5em;
            color: #{theme.get('accent', '00D4FF')};
            margin-bottom: 10px;
        }}
        .header p {{
            color: #{theme.get('muted', 'A1A1AA')};
            font-size: 1.1em;
        }}
        .slides-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 24px;
        }}
        .slide-card {{
            background: #{theme.get('surface', '141414')};
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #{theme.get('muted', 'A1A1AA')}33;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .slide-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 32px #{theme.get('accent', '00D4FF')}22;
        }}
        .slide-number {{
            display: inline-block;
            background: #{theme.get('accent', '00D4FF')};
            color: #{theme.get('background', '0A0A0A')};
            width: 32px;
            height: 32px;
            border-radius: 50%;
            text-align: center;
            line-height: 32px;
            font-weight: bold;
            margin-bottom: 12px;
        }}
        .slide-kind {{
            display: inline-block;
            background: #{theme.get('primary', '0A0A0A')};
            color: #{theme.get('accent', '00D4FF')};
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85em;
            margin-left: 8px;
        }}
        .slide-title {{
            font-family: {theme.get('headerFont', 'Arial Black')}, sans-serif;
            font-size: 1.4em;
            margin: 12px 0;
            color: #{theme.get('text', 'FFFFFF')};
        }}
        .slide-intent {{
            color: #{theme.get('muted', 'A1A1AA')};
            font-size: 0.95em;
            margin-bottom: 16px;
            font-style: italic;
        }}
        .bullets {{
            list-style: none;
            margin-bottom: 16px;
        }}
        .bullets li {{
            padding: 8px 0 8px 20px;
            position: relative;
            border-bottom: 1px solid #{theme.get('muted', 'A1A1AA')}22;
        }}
        .bullets li:before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: #{theme.get('accent', '00D4FF')};
        }}
        .speaker-notes {{
            background: #{theme.get('background', '0A0A0A')};
            padding: 12px;
            border-radius: 8px;
            font-size: 0.9em;
            color: #{theme.get('muted', 'A1A1AA')};
            margin-top: 12px;
        }}
        .speaker-notes:before {{
            content: "🎤 演讲备注";
            display: block;
            color: #{theme.get('accent', '00D4FF')};
            margin-bottom: 8px;
            font-weight: bold;
        }}
        .visual-suggestion {{
            margin-top: 12px;
            padding: 8px 12px;
            background: #{theme.get('accent', '00D4FF')}11;
            border-left: 3px solid #{theme.get('accent', '00D4FF')};
            border-radius: 0 8px 8px 0;
            font-size: 0.9em;
        }}
        .review-section {{
            margin-top: 40px;
            padding: 24px;
            background: #{theme.get('surface', '141414')};
            border-radius: 12px;
        }}
        .review-section h2 {{
            color: #{theme.get('accent', '00D4FF')};
            margin-bottom: 16px;
        }}
        .review-notes {{
            list-style: none;
        }}
        .review-notes li {{
            padding: 8px 0;
            border-bottom: 1px solid #{theme.get('muted', 'A1A1AA')}22;
        }}
        .action-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #{theme.get('surface', '141414')};
            padding: 16px;
            text-align: center;
            box-shadow: 0 -4px 16px rgba(0,0,0,0.3);
        }}
        .btn {{
            padding: 12px 32px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            margin: 0 8px;
            transition: opacity 0.2s;
        }}
        .btn:hover {{ opacity: 0.9; }}
        .btn-primary {{
            background: #{theme.get('accent', '00D4FF')};
            color: #{theme.get('background', '0A0A0A')};
        }}
        .btn-secondary {{
            background: #{theme.get('muted', 'A1A1AA')};
            color: #{theme.get('background', '0A0A0A')};
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{deck.get('title', 'PPT预览')}</h1>
            <p>受众：{deck.get('audience', '通用商业受众')} | 风格：{deck.get('style', 'consulting')} | 共 {len(slides)} 页</p>
        </div>

        <div class="slides-grid">
"""

    for slide in slides:
        bullets_html = ""
        for bullet in slide.get("bullets", []):
            bullets_html += f'            <li>{bullet}</li>\n'

        html += f"""
            <div class="slide-card">
                <span class="slide-number">{slide.get('index', '')}</span>
                <span class="slide-kind">{slide.get('kind', '')}</span>
                <h3 class="slide-title">{slide.get('title', '')}</h3>
                <p class="slide-intent">{slide.get('intent', '')}</p>
                <ul class="bullets">
{bullets_html}                </ul>
                <div class="speaker-notes">{slide.get('speaker_notes', '')}</div>
                <div class="visual-suggestion">🎨 {slide.get('visual', '')}</div>
            </div>
"""

    html += """
        </div>

        <div class="review-section">
            <h2>📋 审查意见</h2>
            <ul class="review-notes">
"""

    for note in deck.get("review_notes", []):
        html += f"                <li>{note}</li>\n"

    html += """
            </ul>
        </div>
    </div>

    <div class="action-bar">
        <button class="btn btn-primary" onclick="confirmGeneration()">✅ 确认生成PPTX</button>
        <button class="btn btn-secondary" onclick="window.close()">❌ 取消</button>
    </div>

    <script>
        function confirmGeneration() {
            if (confirm('确认要生成PPTX文件吗？')) {
                fetch('/api/confirm', { method: 'POST' })
                    .then(() => alert('PPTX生成已启动，请查看outputs目录'))
                    .catch(() => alert('请在命令行中确认生成'));
            }
        }
    </script>
</body>
</html>"""

    _write_html("/workspace/preview.html", html)
    return "/workspace/preview.html"


def render_pptx(deck_json_path: str = "/workspace/deck.json") -> str:
    """调用Node.js脚本渲染PPTX文件。"""
    deck_path = Path(deck_json_path)
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "render_deck.cjs"

    if not script_path.exists():
        raise RuntimeError(f"缺少渲染脚本：{script_path}")

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(deck_path, out_dir / "deck.json")

    result = subprocess.run(
        ["node", str(script_path), str(out_dir / "deck.json"), str(out_dir / "deck.pptx")],
        cwd=str(script_path.parents[1]),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"PPTX渲染失败：{result.stderr or result.stdout}")

    return str(out_dir / "deck.pptx")


def _write_json(path: str, data: Any) -> None:
    # 将绝对路径转换为相对路径
    if path.startswith("/workspace/"):
        path = path[1:]  # 移除开头的/，变成相对路径
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_html(path: str, content: str) -> None:
    if path.startswith("/workspace/"):
        path = path[1:]
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _title_for(kind: str, topic: str) -> str:
    titles = {
        "title": topic,
        "context": "为什么现在是关键窗口",
        "problem": "当前痛点正在形成明确机会",
        "insight": "核心判断",
        "framework": "PPT Agent 能力架构",
        "evidence": "趋势与证据",
        "roadmap": "落地路线图",
        "deep_dive": "关键议题展开",
        "closing": "结论与下一步",
    }
    return titles.get(kind, topic)


def _bullets_for(kind: str, brief: dict, insights: list[str]) -> list[str]:
    defaults = {
        "title": [f"面向{brief['audience']}", f"{brief['style']}风格演示"],
        "context": ["需求从单点生成走向端到端交付", "企业更关注可编辑、可追溯、可复用", "Agent 适合承接多步骤内容工作流"],
        "problem": ["资料分散导致准备成本高", "内容、设计和格式之间缺少统一编排", "模板与品牌规范难以稳定执行"],
        "insight": insights[:3],
        "framework": ["Brief 理解", "资料研究", "大纲规划", "页面写作", "设计渲染", "审稿迭代"],
        "evidence": ["以市场产品能力作为参照", "以企业模板和内部资料作为壁垒", "以导出质量和可编辑性作为交付标准"],
        "roadmap": ["MVP：主题到 PPTX", "增强：资料/RAG/模板", "生产化：权限、审计、视觉 QA"],
        "deep_dive": ["聚焦一个高价值场景", "明确输入、输出和验收标准", "沉淀为可复用 skill"],
        "closing": ["先做垂直场景闭环", "用结构化 deck JSON 管控质量", "逐步叠加企业级能力"],
    }
    return defaults.get(kind, insights[:3])[:5]


def _visual_for(kind: str) -> str:
    visuals = {
        "title": "大标题封面，弱化装饰，突出主题",
        "context": "三段式趋势卡片",
        "problem": "痛点矩阵",
        "insight": "重点结论页",
        "framework": "从输入到输出的流程图",
        "evidence": "数据图表或案例对比",
        "roadmap": "三阶段路线图",
        "deep_dive": "左右分栏分析",
        "closing": "结论摘要和行动项",
    }
    return visuals.get(kind, "标题加正文")
