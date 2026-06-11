from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import ppt_router, ws_router

app = FastAPI(
    title="PPT Agent API",
    description="智能PPT生成工具API",
    version="1.0.0",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(ppt_router)
app.include_router(ws_router)

# 静态文件服务（用于预览）
app.mount("/workspace", StaticFiles(directory="workspace"), name="workspace")


@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "PPT Agent API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
