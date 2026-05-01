"""
src/utils/config.py
Centralised configuration using pydantic-settings.
All settings are loaded from environment variables / .env file.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    output_dir: Path = Path("./output")
    temp_dir: Path = Path("./tmp")
    max_video_duration: int = Field(300, ge=1, le=600)
    default_video_resolution: str = "1920x1080"
    default_fps: int = 30

    # ── OpenAI ───────────────────────────────────────────
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_image_model: str = "dall-e-3"
    openai_tts_model: str = "tts-1-hd"
    openai_whisper_model: str = "whisper-1"

    # ── ElevenLabs ───────────────────────────────────────
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # default: Rachel

    # ── Stability AI ─────────────────────────────────────
    stability_api_key: str = ""
    stability_engine: str = "stable-diffusion-xl-1024-v1-0"

    # ── Kling AI ─────────────────────────────────────────
    kling_api_key: str = ""
    kling_api_secret: str = ""

    # ── Runway ────────────────────────────────────────────
    runway_api_key: str = ""

    # ── Azure TTS ────────────────────────────────────────
    azure_speech_key: str = ""
    azure_speech_region: str = "eastus"

    # ── AWS S3 ───────────────────────────────────────────
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-east-1"
    s3_bucket_name: str = "ai-video-outputs"

    # ── API Server ───────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    cors_origins: List[str] = ["http://localhost:3000"]

    def ensure_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


# Singleton
settings = Settings()
settings.ensure_dirs()
