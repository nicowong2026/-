"""
src/api/routes.py
FastAPI route handlers.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from src.agent import AgentConfig, VideoAgent
from src.api.schemas import (
    CreateVideoRequest,
    CreateVideoResponse,
    TaskStatus,
    TaskStatusResponse,
)
from src.utils.logger import logger

router = APIRouter(prefix="/v1", tags=["Video Generation"])

# In-memory task store (replace with Redis/DB in production)
_tasks: Dict[str, TaskStatusResponse] = {}


async def _run_pipeline(task_id: str, request: CreateVideoRequest) -> None:
    """Background worker that runs the video generation pipeline."""
    _tasks[task_id].status = TaskStatus.running

    try:
        config = AgentConfig(
            image_backend=request.image_backend,
            video_backend=request.video_backend,
            audio_backend=request.audio_backend,
            style=request.style.value,  # type: ignore[arg-type]
        )
        agent = VideoAgent(config)
        result = await agent.create(
            prompt=request.prompt,
            duration=request.duration,
            voice=request.voice,
            subtitles=request.subtitles,
        )
        _tasks[task_id].status = TaskStatus.completed
        _tasks[task_id].progress = 1.0
        _tasks[task_id].output_url = f"/v1/download/{task_id}"
        _tasks[task_id].script = result.script
        _tasks[task_id].scenes = result.scenes
        # Store path for download
        _tasks[task_id].error = str(result.output_path)  # reuse field as storage hack
        logger.success(f"[API] Task {task_id} completed")
    except Exception as exc:
        logger.exception(f"[API] Task {task_id} failed: {exc}")
        _tasks[task_id].status = TaskStatus.failed
        _tasks[task_id].error = str(exc)


@router.post("/videos", response_model=CreateVideoResponse, status_code=202)
async def create_video(
    request: CreateVideoRequest, background_tasks: BackgroundTasks
) -> CreateVideoResponse:
    """Submit a new video generation task."""
    task_id = uuid.uuid4().hex
    _tasks[task_id] = TaskStatusResponse(task_id=task_id, status=TaskStatus.pending)
    background_tasks.add_task(_run_pipeline, task_id, request)
    return CreateVideoResponse(task_id=task_id)


@router.get("/videos/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Poll the status of a video generation task."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _tasks[task_id]


@router.get("/download/{task_id}")
async def download_video(task_id: str) -> FileResponse:
    """Download the generated video file."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    task = _tasks[task_id]
    if task.status != TaskStatus.completed:
        raise HTTPException(status_code=400, detail=f"Task status: {task.status}")
    # output path stored in error field (quick hack for demo)
    output_path = task.error
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"ai_video_{task_id[:8]}.mp4",
    )
