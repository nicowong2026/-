"""
src/api/schemas.py
Pydantic request/response models for the REST API.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class VideoStyle(str, Enum):
    cinematic = "cinematic"
    anime = "anime"
    realistic = "realistic"
    cartoon = "cartoon"
    documentary = "documentary"


class CreateVideoRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=500, examples=["一只熊猫在竹林中漫步"])
    duration: int = Field(15, ge=3, le=120, description="Target video length in seconds")
    style: VideoStyle = VideoStyle.cinematic
    voice: str = Field("zh-CN-XiaoxiaoNeural", description="TTS voice identifier")
    subtitles: bool = Field(True, description="Auto-generate and embed subtitles")
    image_backend: str = Field("openai", description="openai | stability | local")
    video_backend: str = Field("kling", description="kling | runway | local")
    audio_backend: str = Field("edge", description="openai | elevenlabs | edge | azure")


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class CreateVideoResponse(BaseModel):
    task_id: str
    status: TaskStatus = TaskStatus.pending
    message: str = "Task submitted successfully"


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: float = Field(0.0, ge=0, le=1.0)
    output_url: Optional[str] = None
    error: Optional[str] = None
    script: Optional[str] = None
    scenes: Optional[List[str]] = None
