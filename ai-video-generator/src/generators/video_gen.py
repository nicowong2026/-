"""
src/generators/video_gen.py
Image-to-video / text-to-video generation with multi-backend support.

Supported backends:
- kling  : Kling AI API (recommended for Chinese users)
- runway : Runway Gen-3 Alpha API
- local  : CogVideoX via diffusers (requires GPU extras)
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Literal, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import settings
from src.utils.file_utils import make_temp_path
from src.utils.logger import logger

Backend = Literal["kling", "runway", "local"]


class VideoGenerator:
    """Generate short video clips from an image or text prompt."""

    def __init__(self, backend: Backend = "kling") -> None:
        self.backend = backend

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        *,
        image_path: Optional[Path] = None,
        duration: int = 5,
        fps: int = 24,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Generate a video clip and return the path to the output file.

        Args:
            prompt:      Text description of the desired video.
            image_path:  Optional seed image for image-to-video mode.
            duration:    Clip length in seconds (1–10).
            fps:         Frames per second.
            output_path: Where to save the result (auto-generated if None).
        """
        logger.info(f"[VideoGen/{self.backend}] Generating {duration}s clip: {prompt[:80]}…")
        output_path = output_path or make_temp_path(".mp4")

        if self.backend == "kling":
            await self._generate_kling(
                prompt, image_path=image_path, duration=duration, output_path=output_path
            )
        elif self.backend == "runway":
            await self._generate_runway(
                prompt, image_path=image_path, duration=duration, output_path=output_path
            )
        elif self.backend == "local":
            self._generate_local(
                prompt, image_path=image_path, duration=duration, fps=fps, output_path=output_path
            )
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

        logger.success(f"[VideoGen] Saved → {output_path}")
        return output_path

    # ── Backends ──────────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=5, max=30))
    async def _generate_kling(
        self,
        prompt: str,
        *,
        image_path: Optional[Path],
        duration: int,
        output_path: Path,
    ) -> None:
        """
        Kling AI v1 API:
        POST /v1/videos/text2video  (text-to-video)
        POST /v1/videos/image2video (image-to-video)
        Then poll GET /v1/videos/{task_id} until status == "succeed".
        """
        import hashlib
        import hmac
        import jwt  # PyJWT

        # Build JWT token for Kling
        now = int(time.time())
        payload = {
            "iss": settings.kling_api_key,
            "exp": now + 1800,
            "nbf": now - 5,
        }
        token = jwt.encode(payload, settings.kling_api_secret, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        endpoint = "image2video" if image_path else "text2video"
        body: dict = {
            "model_name": "kling-v1",
            "prompt": prompt,
            "duration": str(duration),
            "mode": "std",
        }
        if image_path:
            import base64
            body["image"] = base64.b64encode(image_path.read_bytes()).decode()

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://api.klingai.com/v1/videos/{endpoint}",
                headers=headers,
                json=body,
            )
            resp.raise_for_status()
            task_id = resp.json()["data"]["task_id"]
            logger.debug(f"[Kling] Task submitted: {task_id}")

            # Poll until complete (max 5 minutes)
            for _ in range(60):
                await asyncio.sleep(5)
                poll = await client.get(
                    f"https://api.klingai.com/v1/videos/{task_id}",
                    headers=headers,
                )
                poll.raise_for_status()
                status = poll.json()["data"]["task_status"]
                if status == "succeed":
                    video_url = poll.json()["data"]["task_result"]["videos"][0]["url"]
                    break
                elif status == "failed":
                    raise RuntimeError(f"Kling task failed: {poll.json()}")
            else:
                raise TimeoutError("Kling task timed out after 5 minutes")

            # Download
            dl = await client.get(video_url, timeout=300)
            dl.raise_for_status()
            output_path.write_bytes(dl.content)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=5, max=30))
    async def _generate_runway(
        self,
        prompt: str,
        *,
        image_path: Optional[Path],
        duration: int,
        output_path: Path,
    ) -> None:
        """Runway Gen-3 Alpha API."""
        import base64

        headers = {
            "Authorization": f"Bearer {settings.runway_api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }
        body: dict = {
            "model": "gen3a_turbo",
            "promptText": prompt,
            "duration": duration,
            "ratio": "1280:720",
        }
        if image_path:
            mime = "image/png" if image_path.suffix == ".png" else "image/jpeg"
            b64 = base64.b64encode(image_path.read_bytes()).decode()
            body["promptImage"] = f"data:{mime};base64,{b64}"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.dev.runwayml.com/v1/image_to_video",
                headers=headers,
                json=body,
            )
            resp.raise_for_status()
            task_id = resp.json()["id"]

            for _ in range(120):
                await asyncio.sleep(5)
                poll = await client.get(
                    f"https://api.dev.runwayml.com/v1/tasks/{task_id}",
                    headers=headers,
                )
                poll.raise_for_status()
                data = poll.json()
                if data["status"] == "SUCCEEDED":
                    video_url = data["output"][0]
                    break
                elif data["status"] == "FAILED":
                    raise RuntimeError(f"Runway task failed: {data}")
            else:
                raise TimeoutError("Runway task timed out")

            dl = await client.get(video_url, timeout=300)
            dl.raise_for_status()
            output_path.write_bytes(dl.content)

    def _generate_local(
        self,
        prompt: str,
        *,
        image_path: Optional[Path],
        duration: int,
        fps: int,
        output_path: Path,
    ) -> None:
        """CogVideoX-5B local inference. Requires GPU extras."""
        try:
            import torch
            from diffusers import CogVideoXPipeline
        except ImportError as exc:
            raise ImportError(
                "Install GPU extras: pip install 'ai-video-generator[gpu]'"
            ) from exc

        pipe = CogVideoXPipeline.from_pretrained(
            "THUDM/CogVideoX-5b",
            torch_dtype=torch.bfloat16,
        ).to("cuda")
        pipe.enable_model_cpu_offload()

        num_frames = duration * fps
        video_frames = pipe(
            prompt=prompt,
            num_inference_steps=50,
            num_frames=num_frames,
            guidance_scale=6.0,
        ).frames[0]

        from diffusers.utils import export_to_video
        export_to_video(video_frames, str(output_path), fps=fps)
