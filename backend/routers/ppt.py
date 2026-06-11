from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from ..schemas.ppt import PPTRequest, PPTResponse, SessionStatus
from ..services.ppt_service import generate_ppt_task

router = APIRouter(prefix="/api", tags=["ppt"])

# 内存存储会话状态
sessions: Dict[str, SessionStatus] = {}


@router.post("/sessions", response_model=PPTResponse)
async def create_session(request: PPTRequest, background_tasks: BackgroundTasks):
    """创建PPT生成会话"""
    session_id = str(uuid.uuid4())[:8]

    session = SessionStatus(
        session_id=session_id,
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    sessions[session_id] = session

    # 后台启动生成任务
    background_tasks.add_task(
        generate_ppt_task,
        session_id=session_id,
        params=request.model_dump(),
        sessions=sessions,
    )

    return PPTResponse(
        session_id=session_id,
        status="pending",
        message="PPT生成任务已创建，请通过WebSocket接收进度",
    )


@router.get("/sessions/{session_id}", response_model=SessionStatus)
async def get_session(session_id: str):
    """获取会话状态"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    return sessions[session_id]


@router.post("/sessions/{session_id}/confirm")
async def confirm_generation(session_id: str):
    """确认生成PPTX"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = sessions[session_id]
    if session.status != "completed" or not session.deck:
        raise HTTPException(status_code=400, detail="会话未完成或Deck数据不存在")

    try:
        from ppt_agent.tools import render_pptx
        import asyncio

        deck_path = Path("workspace") / "deck.json"
        pptx_path = await asyncio.to_thread(render_pptx, str(deck_path))

        session.pptx_url = f"/api/sessions/{session_id}/download"
        session.updated_at = datetime.now()

        return {"message": "PPTX生成成功", "download_url": session.pptx_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PPTX生成失败: {str(e)}")


@router.get("/sessions/{session_id}/download")
async def download_pptx(session_id: str):
    """下载PPTX文件"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = sessions[session_id]
    pptx_path = Path("outputs") / "deck.pptx"

    if not pptx_path.exists():
        raise HTTPException(status_code=404, detail="PPTX文件不存在")

    return FileResponse(
        path=str(pptx_path),
        filename=f"ppt_{session_id}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@router.get("/sessions/{session_id}/preview")
async def get_preview(session_id: str):
    """获取HTML预览"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    preview_path = Path("workspace") / "preview.html"
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="预览文件不存在")

    return FileResponse(
        path=str(preview_path),
        media_type="text/html",
    )
