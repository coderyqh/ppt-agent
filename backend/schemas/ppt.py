from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class PPTRequest(BaseModel):
    """PPT生成请求"""
    topic: str = Field(..., description="PPT主题", min_length=1, max_length=200)
    audience: str = Field(default="通用商业受众", description="目标受众", max_length=100)
    slides: int = Field(default=8, description="页数", ge=3, le=30)
    style: str = Field(default="consulting", description="演示风格", max_length=50)
    visual_style: Literal[
        "dark-premium",
        "glassmorphism",
        "gradient-modern",
        "keynote",
        "minimal-swiss",
        "editorial",
        "3d-isometric",
    ] = Field(default="dark-premium", description="视觉风格")
    mode: Literal["rule", "llm", "auto"] = Field(default="rule", description="内容生成模式")
    source_text: Optional[str] = Field(default=None, description="参考资料")


class PPTResponse(BaseModel):
    """PPT生成响应"""
    session_id: str = Field(..., description="会话ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(..., description="状态")
    message: str = Field(..., description="状态消息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class SessionStatus(BaseModel):
    """会话状态"""
    session_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    current_step: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    steps_completed: list[str] = Field(default_factory=list)
    deck: Optional[dict] = None
    preview_url: Optional[str] = None
    pptx_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StepResult(BaseModel):
    """步骤结果"""
    step: str
    status: Literal["success", "failed", "fallback"]
    mode_used: str
    data: Optional[dict] = None
    error: Optional[str] = None
