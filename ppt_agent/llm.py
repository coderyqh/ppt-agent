from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
DEFAULT_MODEL = "mimo-v2.5-pro"


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        self._load_dotenv()

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMError("缺少 openai 依赖，请先运行 pip install -r requirements.txt。") from exc

        api_key = (
            os.getenv("MIMO_API_KEY")
            or os.getenv("MINIMAX_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        if not api_key:
            raise LLMError("缺少 API key。请设置 MIMO_API_KEY、MINIMAX_API_KEY 或 OPENAI_API_KEY。")

        self.model = model or os.getenv("PPT_AGENT_MODEL") or DEFAULT_MODEL
        self.base_url = (
            base_url
            or os.getenv("MIMO_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("MINIMAX_BASE_URL")
            or DEFAULT_BASE_URL
        )
        self.client = OpenAI(api_key=api_key, base_url=self.base_url)

    def create_deck_plan(
        self,
        topic: str,
        audience: str,
        slide_count: int,
        style: str,
        outline: list[dict[str, str]],
        insights: list[str],
        source_text: str = "",
    ) -> dict[str, Any]:
        prompt = self._build_prompt(topic, audience, slide_count, style, outline, insights, source_text)
        request: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是一个专业 PPT 策划 Agent，擅长商业叙事、咨询风结构和可编辑 PPT 内容规划。"
                        "你必须只输出一个 JSON 对象，不输出 Markdown、解释或额外文本。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.35,
            "max_completion_tokens": 4096,
        }
        if "xiaomimimo.com" in self.base_url:
            request["extra_body"] = {"thinking": {"type": "disabled"}}

        response = self.client.chat.completions.create(**request)

        content = response.choices[0].message.content or ""
        data = self._parse_json_object(content)
        self._validate_deck_plan(data, slide_count)
        return data

    def _build_prompt(
        self,
        topic: str,
        audience: str,
        slide_count: int,
        style: str,
        outline: list[dict[str, str]],
        insights: list[str],
        source_text: str,
    ) -> str:
        return f"""
请根据需求生成 PPT deck plan JSON。

输出格式必须完全符合：
{{
  "title": "string",
  "slides": [
    {{
      "kind": "title|context|problem|insight|framework|evidence|roadmap|deep_dive|closing",
      "intent": "string",
      "title": "string",
      "bullets": ["string"],
      "speaker_notes": "string",
      "visual": "string"
    }}
  ]
}}

需求：
- 主题：{topic}
- 受众：{audience}
- 页数：{slide_count}
- 风格：{style}

建议大纲：
{json.dumps(outline, ensure_ascii=False, indent=2)}

已提取洞察：
{json.dumps(insights, ensure_ascii=False, indent=2)}

资料：
{source_text or "暂无额外资料，请基于通用商业逻辑生成。"}

硬性要求：
- slides 数量必须等于 {slide_count}
- 每页 bullets 为 2 到 5 条
- 所有内容使用中文
- 每页只表达一个清晰意图
- 标题要像真实商业 PPT，不要像聊天回答
- visual 写具体视觉建议，例如流程图、矩阵图、路线图、趋势图、对比表
- speaker_notes 写给演讲者看的口播提示
- 不要输出 ```json 代码块
- 不要输出 JSON 以外的任何字符
"""

    def _parse_json_object(self, content: str) -> dict[str, Any]:
        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise LLMError("模型没有返回可解析的 JSON 对象。")
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError as exc:
                raise LLMError(f"模型返回了无效 JSON：{exc}") from exc

    def _validate_deck_plan(self, data: dict[str, Any], slide_count: int) -> None:
        slides = data.get("slides")
        if not isinstance(slides, list):
            raise LLMError("模型返回 JSON 缺少 slides 数组。")
        if len(slides) != slide_count:
            raise LLMError(f"模型返回 {len(slides)} 页，但请求是 {slide_count} 页。")

        required = {"kind", "intent", "title", "bullets", "speaker_notes", "visual"}
        for idx, slide in enumerate(slides, start=1):
            if not isinstance(slide, dict):
                raise LLMError(f"第 {idx} 页不是对象。")
            missing = required - set(slide)
            if missing:
                raise LLMError(f"第 {idx} 页缺少字段：{', '.join(sorted(missing))}。")
            if not isinstance(slide["bullets"], list) or not 1 <= len(slide["bullets"]) <= 5:
                raise LLMError(f"第 {idx} 页 bullets 必须是 1 到 5 条。")

    def extract_insights_from_text(self, topic: str, source_text: str, audience: str) -> list[str]:
        """用LLM从资料中提取关键洞察。"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是商业分析专家。只输出JSON数组。"},
                {"role": "user", "content": f"""
从以下资料中提取 3-8 条关键洞察，面向{audience}，围绕"{topic}"。

资料：
{source_text}

输出格式：["洞察1", "洞察2", ...]
要求：每条洞察不超过50字，聚焦商业价值和行动启示。"""},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        content = response.choices[0].message.content or "[]"
        return self._parse_json_array(content)

    def build_outline_for_topic(
        self, topic: str, audience: str, slide_count: int, style: str, insights: list[str]
    ) -> list[dict[str, str]]:
        """用LLM构建叙事大纲。"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是PPT叙事架构师。只输出JSON数组。"},
                {"role": "user", "content": f"""
为以下PPT设计叙事大纲：
- 主题：{topic}
- 受众：{audience}
- 页数：{slide_count}
- 风格：{style}
- 关键洞察：{json.dumps(insights, ensure_ascii=False)}

输出格式：[{{"kind": "title", "intent": "..."}}, ...]
kind可选值：title, context, problem, insight, framework, evidence, roadmap, deep_dive, closing"""},
            ],
            temperature=0.35,
            max_tokens=2048,
        )
        content = response.choices[0].message.content or "[]"
        return self._parse_json_array(content)

    def review_deck_quality(self, deck_json: str) -> list[str]:
        """用LLM进行语义级质量审查。"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是PPT质量审查专家。只输出JSON数组。"},
                {"role": "user", "content": f"""
审查以下PPT Deck，从以下维度给出具体建议：
1. 叙事逻辑是否连贯
2. 每页意图是否清晰
3. 标题是否像真实商业PPT
4. 要点是否精炼有力
5. 演讲备注是否实用

Deck内容：
{deck_json}

输出格式：["问题1", "建议2", ...]
如果质量良好，返回 ["质量检查通过：...（具体优点）"]"""},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        content = response.choices[0].message.content or "[]"
        return self._parse_json_array(content)

    def _parse_json_array(self, content: str) -> list:
        """解析LLM返回的JSON数组。"""
        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start != -1 and end > start:
                return json.loads(cleaned[start:end + 1])
        raise LLMError("模型没有返回可解析的 JSON 数组。")

    def _load_dotenv(self) -> None:
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            return

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
