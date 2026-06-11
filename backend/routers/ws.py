from __future__ import annotations

import json
import logging
from typing import Dict, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("ws_router")

router = APIRouter(tags=["websocket"])

# WebSocket连接管理
connections: Dict[str, Set[WebSocket]] = {}


async def broadcast_to_session(session_id: str, message: dict):
    """向指定会话的所有连接广播消息"""
    if session_id in connections:
        dead_connections = set()
        for ws in connections[session_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"发送消息失败: {e}")
                dead_connections.add(ws)
        # 清理断开的连接
        connections[session_id] -= dead_connections
        if not connections[session_id]:
            del connections[session_id]
            logger.info(f"会话 {session_id} 的所有WebSocket连接已清理")


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket端点，用于流式接收生成进度"""
    logger.info(f"WebSocket连接请求: {session_id}")
    await websocket.accept()

    # 注册连接
    if session_id not in connections:
        connections[session_id] = set()
    connections[session_id].add(websocket)
    logger.info(f"WebSocket连接已建立: {session_id}, 当前连接数: {len(connections[session_id])}")

    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "已连接到进度流",
        })

        # 保持连接，等待消息或断开
        while True:
            # 接收客户端消息（心跳或命令）
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.debug(f"收到客户端消息: {message}")

            # 处理心跳
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket断开连接: {session_id}")
        # 客户端断开连接
        if session_id in connections:
            connections[session_id].discard(websocket)
            if not connections[session_id]:
                del connections[session_id]
    except Exception as e:
        logger.error(f"WebSocket错误: {e}", exc_info=True)
        # 其他错误
        if session_id in connections:
            connections[session_id].discard(websocket)
            if not connections[session_id]:
                del connections[session_id]
