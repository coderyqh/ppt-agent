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
    
    # 获取主题信息用于相关性检查
    deck_title = deck.get("title", "")
    slides = deck.get("slides", [])
    
    # 合法的幻灯片类型
    VALID_SLIDE_KINDS = {"title", "context", "problem", "insight", "framework", "evidence", "roadmap", "deep_dive", "closing"}

    def rule():
        notes = []
        slide_kinds_seen = []
        
        for slide in slides:
            index = slide.get("index", 0)
            kind = slide.get("kind", "")
            title = slide.get("title", "")
            bullets = slide.get("bullets", [])
            
            # 原有检查：标题是否存在
            if not title:
                notes.append(f"第 {index} 页缺少标题。")
            
            # 原有检查：bullets数量 <= 5
            if len(bullets) > 5:
                notes.append(f"第 {index} 页要点过多，建议压缩到 5 条以内。")
            
            # 原有检查：单条bullet长度 <= 42字符
            if any(len(b) > 42 for b in bullets):
                notes.append(f"第 {index} 页存在较长 bullet，建议拆分或改写。")
            
            # 新增检查：bullets是否为空
            if not bullets:
                notes.append(f"第 {index} 页缺少要点内容。")
            
            # 新增检查：幻灯片类型是否合法
            if kind not in VALID_SLIDE_KINDS:
                notes.append(f"第 {index} 页类型 '{kind}' 不合法。")
            
            # 新增检查：标题是否包含主题关键词（简单检查）
            if deck_title and len(deck_title) > 1:
                # 提取主题关键词（去掉常见停用词）
                topic_words = [w for w in deck_title if len(w) > 1 and w not in {"的", "和", "与", "及", "或", "是", "在", "有", "为", "了"}]
                # 检查标题是否至少包含一个主题关键词（非title类型的幻灯片）
                if kind != "title" and topic_words:
                    has_topic_keyword = any(word in title for word in topic_words)
                    if not has_topic_keyword and title:
                        notes.append(f"第 {index} 页标题 '{title}' 可能与主题 '{deck_title}' 相关性较低。")
            
            slide_kinds_seen.append(kind)
        
        # 新增检查：是否有重复的幻灯片类型
        from collections import Counter
        kind_counts = Counter(slide_kinds_seen)
        for kind, count in kind_counts.items():
            if count > 1 and kind not in {"deep_dive", "context"}:
                notes.append(f"幻灯片类型 '{kind}' 出现了 {count} 次，可能存在重复内容。")
        
        # 新增检查：幻灯片数量是否合理
        if len(slides) < 3:
            notes.append(f"幻灯片数量过少（{len(slides)} 页），建议至少 3 页。")
        elif len(slides) > 30:
            notes.append(f"幻灯片数量过多（{len(slides)} 页），建议不超过 30 页。")
        
        return notes or ["基础检查通过：标题、页数、页面密度和主题相关性正常。"]

    def llm(client: LLMClient):
        rule_notes = rule()
        # 传入主题信息用于LLM审核
        llm_notes = client.review_deck_quality(
            json.dumps(deck, ensure_ascii=False),
            topic=deck_title
        )
        return rule_notes + llm_notes

    notes, mode_used = _execute_with_mode(mode, rule, llm)

    deck["review_notes"] = notes
    _write_json("/workspace/deck.json", deck)
    return deck


def generate_html_preview(deck_json: str, mode: str = "rule") -> str:
    """生成HTML预览页面，使用PPT标准16:9比例。"""
    deck = json.loads(deck_json) if isinstance(deck_json, str) else deck_json

    theme = deck.get("theme", {})
    slides = deck.get("slides", [])
    
    # 获取主题配置
    primary = theme.get("primary", "0A0A0A")
    secondary = theme.get("secondary", "1D1D1F")
    accent = theme.get("accent", "00D4FF")
    background = theme.get("background", "0A0A0A")
    surface = theme.get("surface", "141414")
    text_color = theme.get("text", "FFFFFF")
    muted = theme.get("muted", "A1A1AA")
    header_font = theme.get("headerFont", "Arial Black")
    body_font = theme.get("bodyFont", "Arial")
    visual_style = theme.get("deerStyle", "dark-premium")

    # 生成每页幻灯片HTML
    slides_html = ""
    thumbnails_html = ""
    
    for i, slide in enumerate(slides):
        bullets_html = ""
        for bullet in slide.get("bullets", []):
            bullets_html += f'<li class="slide-bullet">{bullet}</li>\n'
        
        # 幻灯片内容
        slides_html += f"""
        <div class="slide" id="slide-{i}" style="display: {'flex' if i == 0 else 'none'}">
            <div class="slide-content">
                <div class="slide-header">
                    <span class="slide-number">{slide.get('index', i+1)}</span>
                    <span class="slide-kind">{slide.get('kind', '')}</span>
                </div>
                <h2 class="slide-title">{slide.get('title', '')}</h2>
                <p class="slide-intent">{slide.get('intent', '')}</p>
                <ul class="slide-bullets">
                    {bullets_html}
                </ul>
                <div class="slide-visual">🎨 {slide.get('visual', '')}</div>
            </div>
            <div class="slide-notes">
                <div class="notes-label">🎤 演讲备注</div>
                <p>{slide.get('speaker_notes', '')}</p>
            </div>
        </div>
"""
        
        # 缩略图
        thumbnails_html += f"""
        <div class="thumbnail {'active' if i == 0 else ''}" onclick="goToSlide({i})">
            <span class="thumb-number">{i+1}</span>
            <span class="thumb-title">{slide.get('title', '')[:10]}...</span>
        </div>
"""

    # 审查意见HTML
    review_html = ""
    for note in deck.get("review_notes", []):
        review_html += f"<li>{note}</li>\n"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{deck.get('title', 'PPT预览')}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Noto Sans SC', {body_font}, sans-serif;
            background: linear-gradient(135deg, #{background} 0%, #{surface} 100%);
            color: #{text_color};
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }}
        
        .presentation-header {{
            text-align: center;
            margin-bottom: 30px;
            width: 100%;
            max-width: 960px;
        }}
        
        .presentation-header h1 {{
            font-family: {header_font}, sans-serif;
            font-size: 2em;
            color: #{accent};
            margin-bottom: 10px;
            text-shadow: 0 2px 10px #{accent}33;
        }}
        
        .presentation-header .meta {{
            color: #{muted};
            font-size: 0.9em;
        }}
        
        .slide-viewer {{
            width: 100%;
            max-width: 960px;
            position: relative;
        }}
        
        .slide {{
            aspect-ratio: 16 / 9;
            width: 100%;
            background: #{surface};
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px #{muted}22;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }}
        
        .slide-content {{
            flex: 1;
            padding: 40px 50px;
            display: flex;
            flex-direction: column;
        }}
        
        .slide-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }}
        
        .slide-number {{
            background: #{accent};
            color: #{background};
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .slide-kind {{
            background: #{primary};
            color: #{accent};
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .slide-title {{
            font-family: {header_font}, sans-serif;
            font-size: 2.2em;
            color: #{text_color};
            margin-bottom: 15px;
            line-height: 1.2;
        }}
        
        .slide-intent {{
            color: #{muted};
            font-size: 0.95em;
            margin-bottom: 25px;
            font-style: italic;
            padding-left: 15px;
            border-left: 3px solid #{accent}44;
        }}
        
        .slide-bullets {{
            list-style: none;
            flex: 1;
        }}
        
        .slide-bullet {{
            padding: 10px 0 10px 30px;
            position: relative;
            font-size: 1.05em;
            line-height: 1.5;
            border-bottom: 1px solid #{muted}11;
        }}
        
        .slide-bullet:before {{
            content: "▸";
            position: absolute;
            left: 5px;
            color: #{accent};
            font-weight: bold;
        }}
        
        .slide-visual {{
            margin-top: auto;
            padding: 12px 16px;
            background: #{accent}0D;
            border-left: 3px solid #{accent};
            border-radius: 0 8px 8px 0;
            font-size: 0.85em;
            color: #{muted};
        }}
        
        .slide-notes {{
            background: #{primary};
            padding: 15px 50px;
            border-top: 1px solid #{muted}22;
        }}
        
        .notes-label {{
            color: #{accent};
            font-size: 0.8em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .slide-notes p {{
            color: #{muted};
            font-size: 0.85em;
            line-height: 1.4;
        }}
        
        .navigation {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-top: 25px;
            width: 100%;
            max-width: 960px;
        }}
        
        .nav-btn {{
            background: #{surface};
            color: #{text_color};
            border: 1px solid #{muted}33;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.95em;
            transition: all 0.2s;
        }}
        
        .nav-btn:hover {{
            background: #{accent};
            color: #{background};
            border-color: #{accent};
        }}
        
        .nav-btn:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}
        
        .page-indicator {{
            color: #{muted};
            font-size: 1em;
            min-width: 80px;
            text-align: center;
        }}
        
        .thumbnails {{
            display: flex;
            gap: 10px;
            margin-top: 25px;
            overflow-x: auto;
            padding: 10px 0;
            width: 100%;
            max-width: 960px;
        }}
        
        .thumbnail {{
            background: #{surface};
            border: 2px solid #{muted}33;
            border-radius: 8px;
            padding: 8px 12px;
            cursor: pointer;
            transition: all 0.2s;
            min-width: 80px;
            text-align: center;
        }}
        
        .thumbnail:hover {{
            border-color: #{accent};
        }}
        
        .thumbnail.active {{
            border-color: #{accent};
            background: #{accent}1A;
        }}
        
        .thumb-number {{
            display: block;
            font-weight: bold;
            color: #{accent};
            font-size: 0.9em;
        }}
        
        .thumb-title {{
            display: block;
            font-size: 0.7em;
            color: #{muted};
            margin-top: 4px;
        }}
        
        .review-section {{
            width: 100%;
            max-width: 960px;
            margin-top: 30px;
            background: #{surface};
            border-radius: 12px;
            padding: 20px 30px;
        }}
        
        .review-section h3 {{
            color: #{accent};
            margin-bottom: 15px;
            font-size: 1em;
        }}
        
        .review-section ul {{
            list-style: none;
        }}
        
        .review-section li {{
            padding: 8px 0;
            color: #{muted};
            font-size: 0.9em;
            border-bottom: 1px solid #{muted}11;
        }}
        
        .action-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #{surface};
            padding: 16px;
            text-align: center;
            box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
            border-top: 1px solid #{muted}22;
            z-index: 100;
        }}
        
        .btn {{
            padding: 12px 32px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            margin: 0 8px;
            transition: all 0.2s;
            font-weight: 500;
        }}
        
        .btn-primary {{
            background: #{accent};
            color: #{background};
        }}
        
        .btn-primary:hover {{
            background: #{accent}DD;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px #{accent}44;
        }}
        
        .btn-secondary {{
            background: #{muted}33;
            color: #{text_color};
        }}
        
        .btn-secondary:hover {{
            background: #{muted}55;
        }}
        
        /* 动画效果 */
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}
        
        .slide {{
            animation: slideIn 0.3s ease-out;
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .slide-content {{
                padding: 25px 30px;
            }}
            
            .slide-title {{
                font-size: 1.6em;
            }}
            
            .slide-bullet {{
                font-size: 0.95em;
            }}
        }}
    </style>
</head>
<body>
    <div class="presentation-header">
        <h1>{deck.get('title', 'PPT预览')}</h1>
        <div class="meta">
            受众：{deck.get('audience', '通用商业受众')} | 
            风格：{deck.get('style', 'consulting')} | 
            视觉风格：{visual_style} | 
            共 {len(slides)} 页
        </div>
    </div>
    
    <div class="slide-viewer">
        {slides_html}
    </div>
    
    <div class="navigation">
        <button class="nav-btn" id="prevBtn" onclick="prevSlide()" disabled>◀ 上一页</button>
        <span class="page-indicator" id="pageIndicator">1 / {len(slides)}</span>
        <button class="nav-btn" id="nextBtn" onclick="nextSlide()" {'disabled' if len(slides) <= 1 else ''}>下一页 ▶</button>
    </div>
    
    <div class="thumbnails">
        {thumbnails_html}
    </div>
    
    <div class="review-section">
        <h3>📋 审查意见</h3>
        <ul>
            {review_html}
        </ul>
    </div>
    
    <div class="action-bar">
        <button class="btn btn-primary" onclick="confirmGeneration()">✅ 确认生成PPTX</button>
        <button class="btn btn-secondary" onclick="window.close()">❌ 关闭预览</button>
    </div>
    
    <script>
        let currentSlide = 0;
        const totalSlides = {len(slides)};
        
        function showSlide(index) {{
            // 隐藏所有幻灯片
            document.querySelectorAll('.slide').forEach(s => s.style.display = 'none');
            // 显示目标幻灯片
            document.getElementById('slide-' + index).style.display = 'flex';
            
            // 更新缩略图状态
            document.querySelectorAll('.thumbnail').forEach((t, i) => {{
                t.classList.toggle('active', i === index);
            }});
            
            // 更新页面指示器
            document.getElementById('pageIndicator').textContent = (index + 1) + ' / ' + totalSlides;
            
            // 更新按钮状态
            document.getElementById('prevBtn').disabled = index === 0;
            document.getElementById('nextBtn').disabled = index === totalSlides - 1;
            
            currentSlide = index;
        }}
        
        function nextSlide() {{
            if (currentSlide < totalSlides - 1) {{
                showSlide(currentSlide + 1);
            }}
        }}
        
        function prevSlide() {{
            if (currentSlide > 0) {{
                showSlide(currentSlide - 1);
            }}
        }}
        
        function goToSlide(index) {{
            showSlide(index);
        }}
        
        // 键盘导航
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {{
                nextSlide();
            }} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{
                prevSlide();
            }}
        }});
        
        function confirmGeneration() {{
            if (confirm('确认要生成PPTX文件吗？')) {{
                // 从URL中提取session_id
                const pathParts = window.location.pathname.split('/');
                const sessionId = pathParts[pathParts.length - 2];
                
                fetch('/api/sessions/' + sessionId + '/confirm', {{ method: 'POST' }})
                    .then(response => {{
                        if (response.ok) {{
                            alert('PPTX生成成功！请在前端页面下载。');
                        }} else {{
                            alert('生成失败，请在前端页面重试。');
                        }}
                    }})
                    .catch(() => alert('请在前端页面确认生成'));
            }}
        }}
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
    topic = brief.get("topic", "")
    audience = brief.get("audience", "通用商业受众")
    style = brief.get("style", "consulting")
    
    defaults = {
        "title": [f"面向{audience}", f"{style}风格演示"],
        "context": [
            f"{topic}领域正在经历快速变革",
            f"市场对{topic}的需求持续增长",
            f"企业需要在{topic}方面建立竞争优势"
        ],
        "problem": [
            f"传统{topic}方案效率低下",
            f"缺乏系统化的{topic}方法论",
            f"{topic}资源配置不合理"
        ],
        "insight": insights[:3] if insights else [
            f"{topic}是未来发展的关键驱动力",
            f"系统化方法能显著提升{topic}效果",
            f"投资{topic}将带来长期回报"
        ],
        "framework": [
            f"需求分析：明确{topic}目标",
            f"方案设计：构建{topic}体系",
            f"执行落地：分阶段推进",
            f"持续优化：迭代改进"
        ],
        "evidence": [
            f"行业案例：领先企业在{topic}方面的实践",
            f"数据支撑：{topic}投资回报率分析",
            f"趋势预测：{topic}未来发展方向"
        ],
        "roadmap": [
            f"第一阶段：{topic}基础建设",
            f"第二阶段：{topic}能力提升",
            f"第三阶段：{topic}价值变现"
        ],
        "deep_dive": [
            f"深入分析{topic}的核心要素",
            f"探讨{topic}的最佳实践",
            f"制定{topic}的行动方案"
        ],
        "closing": [
            f"总结{topic}的核心价值",
            f"明确下一步行动计划",
            f"展望{topic}的未来发展"
        ],
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
