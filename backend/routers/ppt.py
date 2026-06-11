from __future__ import annotations

import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from ..schemas.ppt import PPTRequest, PPTResponse, SessionStatus
from ..services.ppt_service import generate_ppt_task

logger = logging.getLogger("ppt_router")

router = APIRouter(prefix="/api", tags=["ppt"])

# 内存存储会话状态
sessions: Dict[str, SessionStatus] = {}


@router.post("/sessions", response_model=PPTResponse)
async def create_session(request: PPTRequest, background_tasks: BackgroundTasks):
    """创建PPT生成会话"""
    session_id = str(uuid.uuid4())[:8]
    logger.info(f"创建会话 {session_id}, 请求参数: {request.model_dump()}")

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

    logger.info(f"会话 {session_id} 已创建，后台任务已启动")

    return PPTResponse(
        session_id=session_id,
        status="pending",
        message="PPT生成任务已创建，请通过WebSocket接收进度",
    )


@router.get("/sessions/{session_id}", response_model=SessionStatus)
async def get_session(session_id: str):
    """获取会话状态"""
    logger.info(f"查询会话状态: {session_id}")
    if session_id not in sessions:
        logger.warning(f"会话不存在: {session_id}")
        raise HTTPException(status_code=404, detail="会话不存在")
    return sessions[session_id]


@router.post("/sessions/{session_id}/confirm")
async def confirm_generation(session_id: str):
    """确认生成PPTX"""
    logger.info(f"确认生成PPTX: {session_id}")
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = sessions[session_id]
    if session.status != "completed" or not session.deck:
        logger.warning(f"会话状态不正确: {session.status}")
        raise HTTPException(status_code=400, detail="会话未完成或Deck数据不存在")

    try:
        from ppt_agent.tools import render_pptx
        import asyncio

        deck_path = Path("workspace") / "deck.json"
        logger.info(f"开始渲染PPTX: {deck_path}")
        pptx_path = await asyncio.to_thread(render_pptx, str(deck_path))
        logger.info(f"PPTX渲染完成: {pptx_path}")

        session.pptx_url = f"/api/sessions/{session_id}/download"
        session.updated_at = datetime.now()

        return {"message": "PPTX生成成功", "download_url": session.pptx_url}
    except Exception as e:
        logger.error(f"PPTX渲染失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PPTX生成失败: {str(e)}")


@router.get("/sessions/{session_id}/download")
async def download_pptx(session_id: str):
    """下载PPTX文件"""
    logger.info(f"下载PPTX: {session_id}")
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = sessions[session_id]
    pptx_path = Path("outputs") / "deck.pptx"

    if not pptx_path.exists():
        logger.warning(f"PPTX文件不存在: {pptx_path}")
        raise HTTPException(status_code=404, detail="PPTX文件不存在")

    return FileResponse(
        path=str(pptx_path),
        filename=f"ppt_{session_id}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@router.get("/sessions/{session_id}/preview")
async def get_preview(session_id: str):
    """获取HTML预览"""
    logger.info(f"获取预览: {session_id}")
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    preview_path = Path("workspace") / "preview.html"
    if not preview_path.exists():
        logger.warning(f"预览文件不存在: {preview_path}")
        raise HTTPException(status_code=404, detail="预览文件不存在")

    return FileResponse(
        path=str(preview_path),
        media_type="text/html",
    )


@router.get("/test-llm")
async def test_llm_connection():
    """测试大模型接口是否正常"""
    logger.info("测试LLM接口连接...")
    
    try:
        from ppt_agent.llm import LLMClient, LLMError
        
        # 尝试创建LLM客户端
        try:
            client = LLMClient()
            logger.info(f"LLM客户端创建成功，模型: {client.model}, Base URL: {client.base_url}")
        except LLMError as e:
            logger.error(f"LLM客户端创建失败: {e}")
            return {
                "status": "error",
                "message": f"LLM客户端创建失败: {str(e)}",
                "details": {
                    "error_type": "config_error",
                    "suggestion": "请检查环境变量 MIMO_API_KEY 或 OPENAI_API_KEY 是否正确设置"
                }
            }
        
        # 尝试发送测试请求
        try:
            import asyncio
            
            def test_request():
                response = client.client.chat.completions.create(
                    model=client.model,
                    messages=[
                        {"role": "user", "content": "你好，请回复'OK'"}
                    ],
                    max_tokens=10,
                    temperature=0
                )
                return response.choices[0].message.content
            
            result = await asyncio.to_thread(test_request)
            logger.info(f"LLM测试请求成功，响应: {result}")
            
            return {
                "status": "success",
                "message": "LLM接口连接正常",
                "details": {
                    "model": client.model,
                    "base_url": client.base_url,
                    "test_response": result
                }
            }
        except Exception as e:
            logger.error(f"LLM测试请求失败: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"LLM测试请求失败: {str(e)}",
                "details": {
                    "error_type": "api_error",
                    "model": client.model,
                    "base_url": client.base_url,
                    "suggestion": "请检查API密钥是否有效，以及网络连接是否正常"
                }
            }
    except Exception as e:
        logger.error(f"测试LLM接口时发生未知错误: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"测试失败: {str(e)}",
            "details": {
                "error_type": "unknown_error"
            }
        }
