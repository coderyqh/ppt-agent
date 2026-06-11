from __future__ import annotations

from pathlib import Path

from deepagents import create_deep_agent

from .tools import (
    create_brief,
    extract_insights,
    build_outline,
    write_slides,
    apply_design,
    review_deck,
    generate_html_preview,
    render_pptx,
)


def create_ppt_agent(
    model: str = "openai:mimo-v2.5-pro",
    visual_style: str = "dark-premium",
) -> any:
    """创建基于 deepagents 的 PPT Agent。"""

    tools = [
        create_brief,
        extract_insights,
        build_outline,
        write_slides,
        apply_design,
        review_deck,
        generate_html_preview,
        render_pptx,
    ]

    system_prompt = """你是一个专业的PPT生成Agent。你的任务是根据用户需求自动生成高质量的商业PPT。

工作流程：
1. 使用 create_brief 解析用户需求
2. 使用 extract_insights 提取资料洞察
3. 使用 build_outline 构建叙事大纲
4. 使用 write_slides 生成每页内容
5. 使用 apply_design 应用视觉主题
6. 使用 review_deck 质量检查
7. 使用 generate_html_preview 生成HTML预览
8. 等待用户确认后再使用 render_pptx 渲染最终PPTX文件

## 模式选择（重要）

以下工具支持 mode 参数，可选值："rule"（默认）、"llm"、"auto"：
- extract_insights
- build_outline
- write_slides
- review_deck

### 选择指南：
- 用户要求"高质量/精细/专业"内容时 → 使用 mode="llm"
- 用户要求"快速/草稿/测试"时 → 使用 mode="rule"
- 用户未明确要求时 → 使用 mode="auto"（优先LLM，失败回退规则）
- 资料丰富（source_text > 200字）时 → 建议 extract_insights 使用 mode="llm"
- 简单主题（3-5页）时 → mode="rule" 通常足够
- 复杂主题（8页以上）时 → 建议 write_slides 使用 mode="llm"

### 示例：
```python
extract_insights(brief_json, mode="llm")
write_slides(brief_json, outline_json, insights_json, mode="auto")
review_deck(deck_json, mode="llm")
```

## 用户交互

- 生成HTML预览后，必须等待用户确认
- 用户可能要求修改某些页面
- 根据反馈迭代优化

使用 write_todos 工具跟踪进度。所有中间结果保存到 workspace/ 目录。
所有文本内容必须使用中文。"""

    agent = create_deep_agent(
        model=model,
        tools=tools,
        skills=[str(Path.cwd() / ".agents" / "skills")],
        system_prompt=system_prompt,
    )

    return agent
