"""
src/generators/image_gen.py
Text-to-image generation with multi-backend support.

Supported backends:
- openai   : DALL·E 3 via OpenAI API
- stability: Stable Diffusion XL via Stability AI REST API
- local    : Diffusers pipeline (requires GPU extras)
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Literal, Optional

import httpx
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import settings
from src.utils.file_utils import make_temp_path
from src.utils.logger import logger

Backend = Literal["openai", "stability", "local"]


class ImageGenerator:
    """Generate images from text prompts."""

    def __init__(self, backend: Backend = "openai") -> None:
        self.backend = backend
        self._openai: Optional[AsyncOpenAI] = None

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        guidance: float = 7.5,
        seed: Optional[int] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Generate an image from *prompt* and save it to *output_path*.

        Returns the path to the saved PNG file.
        """
        logger.info(f"[ImageGen/{self.backend}] Generating image: {prompt[:80]}…")
        output_path = output_path or make_temp_path(".png")

        if self.backend == "openai":
            await self._generate_openai(prompt, output_path, width=width, height=height)
        elif self.backend == "stability":
            await self._generate_stability(
                prompt,
                negative_prompt=negative_prompt,
                output_path=output_path,
                width=width,
                height=height,
                steps=steps,
                guidance=guidance,
                seed=seed,
            )
        elif self.backend == "local":
            self._generate_local(
                prompt,
                negative_prompt=negative_prompt,
                output_path=output_path,
                width=width,
                height=height,
                steps=steps,
                guidance=guidance,
                seed=seed,
            )
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

        logger.success(f"[ImageGen] Saved → {output_path}")
        return output_path

    # ── Backends ──────────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _generate_openai(
        self, prompt: str, output_path: Path, *, width: int, height: int
    ) -> None:
        if self._openai is None:
            self._openai = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        size_map = {
            (1024, 1024): "1024x1024",
            (1792, 1024): "1792x1024",
            (1024, 1792): "1024x1792",
        }
        size = size_map.get((width, height), "1024x1024")
        response = await self._openai.images.generate(
            model=settings.openai_image_model,
            prompt=prompt,
            size=size,  # type: ignore[arg-type]
            response_format="b64_json",
            quality="hd",
            n=1,
        )
        img_bytes = base64.b64decode(response.data[0].b64_json)  # type: ignore[arg-type]
        output_path.write_bytes(img_bytes)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _generate_stability(
        self,
        prompt: str,
        *,
        negative_prompt: str,
        output_path: Path,
        width: int,
        height: int,
        steps: int,
        guidance: float,
        seed: Optional[int],
    ) -> None:
        url = (
            f"https://api.stability.ai/v1/generation/"
            f"{settings.stability_engine}/text-to-image"
        )
        payload: dict = {
            "text_prompts": [
                {"text": prompt, "weight": 1.0},
            ],
            "cfg_scale": guidance,
            "width": width,
            "height": height,
            "steps": steps,
            "samples": 1,
        }
        if negative_prompt:
            payload["text_prompts"].append({"text": negative_prompt, "weight": -1.0})
        if seed is not None:
            payload["seed"] = seed

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.stability_api_key}",
                    "Accept": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        img_bytes = base64.b64decode(data["artifacts"][0]["base64"])
        output_path.write_bytes(img_bytes)

    def _generate_local(
        self,
        prompt: str,
        *,
        negative_prompt: str,
        output_path: Path,
        width: int,
        height: int,
        steps: int,
        guidance: float,
        seed: Optional[int],
    ) -> None:
        """Run Stable Diffusion locally via diffusers. Requires GPU extras."""
        try:
            import torch
            from diffusers import StableDiffusionXLPipeline
        except ImportError as exc:
            raise ImportError(
                "Install GPU extras: pip install 'ai-video-generator[gpu]'"
            ) from exc

        generator = torch.Generator().manual_seed(seed) if seed else None
        pipe = StableDiffusionXLPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16,
        ).to("cuda")
        image = pipe(
            prompt,
            negative_prompt=negative_prompt or None,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=generator,
        ).images[0]
        image.save(output_path)
