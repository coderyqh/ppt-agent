from __future__ import annotations

from .models import Brief, Deck, Slide


class BriefSkill:
    def create(self, topic: str, audience: str, slide_count: int, style: str, source_text: str = "") -> Brief:
        slide_count = max(3, min(slide_count, 30))
        return Brief(
            topic=topic.strip(),
            audience=audience.strip() or "通用商业受众",
            slide_count=slide_count,
            style=style.strip() or "consulting",
            source_text=source_text.strip(),
        )


class ResearchSkill:
    def extract_insights(self, brief: Brief) -> list[str]:
        if not brief.source_text:
            return [
                f"{brief.topic} 的价值需要围绕受众关心的问题展开。",
                "好的商业演示应先建立背景，再提出判断，最后给出行动建议。",
                "页面应控制信息密度，让每页只有一个清晰意图。",
            ]

        lines = [line.strip("- ").strip() for line in brief.source_text.splitlines()]
        insights = [line for line in lines if len(line) >= 8]
        return insights[:8] or [brief.source_text[:120]]


class OutlineSkill:
    def build_outline(self, brief: Brief, insights: list[str]) -> list[dict[str, str]]:
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

        if brief.slide_count <= len(base):
            selected = base[: brief.slide_count]
        else:
            selected = base[:-1]
            extra_count = brief.slide_count - len(base)
            selected.extend(("deep_dive", f"展开关键议题 {i + 1}") for i in range(extra_count))
            selected.append(base[-1])

        return [{"kind": kind, "intent": intent} for kind, intent in selected]


class SlideWriterSkill:
    def write_slides(self, brief: Brief, outline: list[dict[str, str]], insights: list[str]) -> list[Slide]:
        slides: list[Slide] = []
        for idx, item in enumerate(outline, start=1):
            kind = item["kind"]
            title = self._title_for(kind, brief.topic)
            bullets = self._bullets_for(kind, brief, insights)
            slides.append(
                Slide(
                    index=idx,
                    kind=kind,
                    intent=item["intent"],
                    title=title,
                    bullets=bullets,
                    speaker_notes=f"本页重点：{item['intent']}。面向{brief.audience}，讲清楚它与{brief.topic}的关系。",
                    visual=self._visual_for(kind),
                )
            )
        return slides

    def _title_for(self, kind: str, topic: str) -> str:
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

    def _bullets_for(self, kind: str, brief: Brief, insights: list[str]) -> list[str]:
        defaults = {
            "title": [f"面向{brief.audience}", f"{brief.style}风格演示"],
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

    def _visual_for(self, kind: str) -> str:
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


class LLMSlideWriterSkill:
    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        from .llm import LLMClient

        self.llm = LLMClient(model=model, base_url=base_url)

    def write_slides(self, brief: Brief, outline: list[dict[str, str]], insights: list[str]) -> list[Slide]:
        plan = self.llm.create_deck_plan(
            topic=brief.topic,
            audience=brief.audience,
            slide_count=brief.slide_count,
            style=brief.style,
            outline=outline,
            insights=insights,
            source_text=brief.source_text,
        )

        slides: list[Slide] = []
        for idx, item in enumerate(plan["slides"], start=1):
            slides.append(
                Slide(
                    index=idx,
                    kind=str(item["kind"]),
                    intent=str(item["intent"]),
                    title=str(item["title"]),
                    bullets=[str(bullet) for bullet in item["bullets"]],
                    speaker_notes=str(item["speaker_notes"]),
                    visual=str(item["visual"]),
                )
            )
        return slides


class DesignSkill:
    def apply(self, brief: Brief, slides: list[Slide], visual_style: str = "dark-premium") -> Deck:
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

        for slide in slides:
            if slide.kind == "title":
                slide.layout = "title"
            elif slide.kind in {"framework", "roadmap"}:
                slide.layout = "diagram"
            else:
                slide.layout = "title_and_content"

        return Deck(
            title=brief.topic,
            audience=brief.audience,
            style=brief.style,
            theme=theme,
            slides=slides,
        )


class ReviewSkill:
    def review(self, deck: Deck) -> Deck:
        notes: list[str] = []
        for slide in deck.slides:
            if not slide.title:
                notes.append(f"第 {slide.index} 页缺少标题。")
            if len(slide.bullets) > 5:
                notes.append(f"第 {slide.index} 页要点过多，建议压缩到 5 条以内。")
            if any(len(bullet) > 42 for bullet in slide.bullets):
                notes.append(f"第 {slide.index} 页存在较长 bullet，建议拆分或改写。")

        if not notes:
            notes.append("基础检查通过：标题、页数和页面密度正常。")

        deck.review_notes = notes
        return deck
