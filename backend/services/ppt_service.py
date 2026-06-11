from __future__ import annotations

import json
import asyncio
from datetime import datetime
from typing import Dict

from ..schemas.ppt import SessionStatus
from ..routers.ws import broadcast_to_session


async def send_progress(session_id: str, message: dict):
    """发送进度消息到WebSocket"""
    await broadcast_to_session(session_id, message)


async def generate_ppt_task(
    session_id: str,
    params: dict,
    sessions: Dict[str, SessionStatus],
):
    """后台PPT生成任务"""
    from ppt_agent.tools import (
        create_brief,
        extract_insights,
        build_outline,
        write_slides,
        apply_design,
        review_deck,
        generate_html_preview,
    )

    session = sessions[session_id]
    session.status = "processing"
    session.updated_at = datetime.now()

    steps = [
        ("brief", "解析需求", create_brief),
        ("insights", "提取洞察", None),
        ("outline", "构建大纲", None),
        ("slides", "生成内容", None),
        ("design", "应用设计", None),
        ("review", "质量检查", None),
        ("preview", "生成预览", None),
    ]

    try:
        # Step 1: 创建Brief
        await send_progress(session_id, {
            "type": "step_start",
            "step": "brief",
            "message": "正在解析需求...",
        })

        brief = await asyncio.to_thread(
            create_brief,
            topic=params["topic"],
            audience=params.get("audience", "通用商业受众"),
            slide_count=params.get("slides", 8),
            style=params.get("style", "consulting"),
            source_text=params.get("source_text", "") or "",
        )

        session.steps_completed.append("brief")
        session.progress = 14.3
        await send_progress(session_id, {
            "type": "step_done",
            "step": "brief",
            "result": brief,
            "progress": session.progress,
        })

        # Step 2: 提取洞察
        await send_progress(session_id, {
            "type": "step_start",
            "step": "insights",
            "message": "正在提取关键洞察...",
        })

        mode = params.get("mode", "rule")
        insights = await asyncio.to_thread(
            extract_insights,
            json.dumps(brief, ensure_ascii=False),
            mode,
        )

        session.steps_completed.append("insights")
        session.progress = 28.6
        await send_progress(session_id, {
            "type": "step_done",
            "step": "insights",
            "result": insights,
            "progress": session.progress,
        })

        # Step 3: 构建大纲
        await send_progress(session_id, {
            "type": "step_start",
            "step": "outline",
            "message": "正在构建叙事大纲...",
        })

        outline = await asyncio.to_thread(
            build_outline,
            json.dumps(brief, ensure_ascii=False),
            json.dumps(insights, ensure_ascii=False),
            mode,
        )

        session.steps_completed.append("outline")
        session.progress = 42.9
        await send_progress(session_id, {
            "type": "step_done",
            "step": "outline",
            "result": outline,
            "progress": session.progress,
        })

        # Step 4: 生成内容
        await send_progress(session_id, {
            "type": "step_start",
            "step": "slides",
            "message": "正在生成每页内容...",
        })

        slides = await asyncio.to_thread(
            write_slides,
            json.dumps(brief, ensure_ascii=False),
            json.dumps(outline, ensure_ascii=False),
            json.dumps(insights, ensure_ascii=False),
            mode,
        )

        session.steps_completed.append("slides")
        session.progress = 57.2
        await send_progress(session_id, {
            "type": "step_done",
            "step": "slides",
            "result": slides,
            "progress": session.progress,
        })

        # Step 5: 应用设计
        await send_progress(session_id, {
            "type": "step_start",
            "step": "design",
            "message": "正在应用视觉主题...",
        })

        deck = await asyncio.to_thread(
            apply_design,
            json.dumps(brief, ensure_ascii=False),
            json.dumps(slides, ensure_ascii=False),
            params.get("visual_style", "dark-premium"),
        )

        session.steps_completed.append("design")
        session.progress = 71.5
        await send_progress(session_id, {
            "type": "step_done",
            "step": "design",
            "result": deck,
            "progress": session.progress,
        })

        # Step 6: 质量检查
        await send_progress(session_id, {
            "type": "step_start",
            "step": "review",
            "message": "正在进行质量检查...",
        })

        reviewed_deck = await asyncio.to_thread(
            review_deck,
            json.dumps(deck, ensure_ascii=False),
            mode,
        )

        session.steps_completed.append("review")
        session.progress = 85.8
        await send_progress(session_id, {
            "type": "step_done",
            "step": "review",
            "result": reviewed_deck,
            "progress": session.progress,
        })

        # Step 7: 生成预览
        await send_progress(session_id, {
            "type": "step_start",
            "step": "preview",
            "message": "正在生成HTML预览...",
        })

        preview_path = await asyncio.to_thread(
            generate_html_preview,
            json.dumps(reviewed_deck, ensure_ascii=False),
        )

        session.steps_completed.append("preview")
        session.progress = 100.0
        session.deck = reviewed_deck
        session.preview_url = f"/api/sessions/{session_id}/preview"
        session.status = "completed"
        session.updated_at = datetime.now()

        await send_progress(session_id, {
            "type": "preview_ready",
            "url": session.preview_url,
            "progress": session.progress,
        })

        await send_progress(session_id, {
            "type": "deck_ready",
            "deck": reviewed_deck,
            "message": "PPT内容生成完成！请确认后生成PPTX文件。",
        })

    except Exception as e:
        session.status = "failed"
        session.error = str(e)
        session.updated_at = datetime.now()

        await send_progress(session_id, {
            "type": "error",
            "message": f"生成失败: {str(e)}",
        })
