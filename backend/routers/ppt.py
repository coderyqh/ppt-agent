from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ppt_agent import FeedbackRequest, PPTAgentV2Pipeline

from ..schemas.ppt import FeedbackPayload, PPTRequest, PPTResponse, SessionStatus
from ..services.ppt_service import generate_ppt_task


logger = logging.getLogger("ppt_router")
router = APIRouter(prefix="/api", tags=["ppt"])
sessions: Dict[str, SessionStatus] = {}


@router.post("/uploads")
async def upload_source(file: UploadFile = File(...)) -> dict[str, str | int]:
    upload_dir = Path("workspace") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload.bin").name
    target = upload_dir / f"{uuid.uuid4().hex[:8]}-{safe_name}"
    content = await file.read()
    target.write_bytes(content)
    return {"filename": safe_name, "path": str(target), "size": len(content)}


@router.post("/sessions", response_model=PPTResponse)
async def create_session(request: PPTRequest, background_tasks: BackgroundTasks) -> PPTResponse:
    session_id = str(uuid.uuid4())[:8]
    session = SessionStatus(
        session_id=session_id,
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    sessions[session_id] = session
    background_tasks.add_task(generate_ppt_task, session_id, request.model_dump(), sessions)
    logger.info("created PPT session %s", session_id)
    return PPTResponse(
        session_id=session_id,
        status="pending",
        message="PPT generation session created. Connect to WebSocket for progress.",
    )


@router.get("/sessions/{session_id}", response_model=SessionStatus)
async def get_session(session_id: str) -> SessionStatus:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/confirm")
async def confirm_generation(session_id: str) -> dict[str, str]:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "completed" or not session.deck:
        raise HTTPException(status_code=400, detail="Session is not completed yet")

    workspace_dir = Path("workspace") / session_id
    output_dir = Path("outputs") / session_id
    try:
        pipeline = PPTAgentV2Pipeline(workspace_dir=workspace_dir, output_dir=output_dir)
        pptx_path = pipeline.export_pptx()
        session.pptx_url = f"/api/sessions/{session_id}/download"
        session.updated_at = datetime.now()
        return {"message": "PPTX exported", "download_url": session.pptx_url, "path": str(pptx_path)}
    except Exception as exc:
        logger.exception("PPTX render failed for session %s", session_id)
        raise HTTPException(status_code=500, detail=f"PPTX export failed: {exc}") from exc


@router.post("/sessions/{session_id}/feedback")
async def apply_session_feedback(session_id: str, feedback: FeedbackPayload) -> dict[str, str]:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "completed" or not session.deck:
        raise HTTPException(status_code=400, detail="Session is not completed yet")

    pipeline = PPTAgentV2Pipeline(workspace_dir=Path("workspace") / session_id, output_dir=Path("outputs") / session_id)
    try:
        deck_path = pipeline.apply_feedback(
            FeedbackRequest(
                action=feedback.action,
                instruction=feedback.instruction,
                slide_id=feedback.slide_id,
                payload=feedback.payload,
            )
        )
        import json

        session.deck = json.loads(deck_path.read_text(encoding="utf-8"))
        session.updated_at = datetime.now()
        return {"message": "Feedback applied", "deck_path": str(deck_path)}
    except Exception as exc:
        logger.exception("Feedback failed for session %s", session_id)
        raise HTTPException(status_code=500, detail=f"Feedback failed: {exc}") from exc


@router.get("/sessions/{session_id}/download")
async def download_pptx(session_id: str) -> FileResponse:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    pptx_path = Path("outputs") / session_id / "deck.pptx"
    if not pptx_path.exists():
        raise HTTPException(status_code=404, detail="PPTX does not exist. Export first.")
    return FileResponse(
        path=str(pptx_path),
        filename=f"ppt_{session_id}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@router.get("/sessions/{session_id}/preview")
async def get_preview(session_id: str) -> FileResponse:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    preview_path = Path("workspace") / session_id / "preview.html"
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="Preview does not exist")
    return FileResponse(path=str(preview_path), media_type="text/html")


@router.get("/sessions/{session_id}/artifacts")
async def list_artifacts(session_id: str) -> dict:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    manifest = Path("workspace") / session_id / "artifacts.json"
    if not manifest.exists():
        return {"artifacts": []}
    import json

    return {"artifacts": json.loads(manifest.read_text(encoding="utf-8"))}


@router.get("/test-llm")
async def test_llm_connection() -> dict:
    logger.info("Testing LLM connection...")
    try:
        from ppt_agent.llm import LLMClient

        client = LLMClient()
        logger.info(f"LLM client created: model={client.model}, base_url={client.base_url}")

        # 发送测试请求验证API连通性
        def test_request():
            request_params = {
                "model": client.model,
                "messages": [{"role": "user", "content": "Hello, reply 'OK' only."}],
                "temperature": 0,
            }
            if "xiaomimimo.com" in client.base_url:
                request_params["max_completion_tokens"] = 10
                request_params["extra_body"] = {"thinking": {"type": "disabled"}}
            else:
                request_params["max_tokens"] = 10

            response = client.client.chat.completions.create(**request_params)
            return response.choices[0].message.content

        import asyncio
        result = await asyncio.to_thread(test_request)
        logger.info(f"LLM test response: {result}")

        return {
            "status": "success",
            "message": "API key and LLM connection verified",
            "details": {
                "model": client.model,
                "base_url": client.base_url,
                "test_response": result or "(empty response)",
            },
        }
    except Exception as exc:
        logger.error(f"LLM test failed: {exc}", exc_info=True)
        return {
            "status": "error",
            "message": f"LLM connection test failed: {exc}",
            "details": {"suggestion": "Check MIMO_API_KEY / OPENAI_API_KEY and base URL settings."},
        }
