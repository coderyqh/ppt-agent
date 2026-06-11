from __future__ import annotations

import json
from typing import Dict, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
            except Exception:
                dead_connections.add(ws)
        # 清理断开的连接
        connections[session_id] -= dead_connections
        if not connections[session_id]:
            del connections[session_id]


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket端点，用于流式接收生成进度"""
    await websocket.accept()

    # 注册连接
    if session_id not in connections:
        connections[session_id] = set()
    connections[session_id].add(websocket)

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

            # 处理心跳
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        # 客户端断开连接
        if session_id in connections:
            connections[session_id].discard(websocket)
            if not connections[session_id]:
                del connections[session_id]
    except Exception:
        # 其他错误
        if session_id in connections:
            connections[session_id].discard(websocket)
            if not connections[session_id]:
                del connections[session_id]
