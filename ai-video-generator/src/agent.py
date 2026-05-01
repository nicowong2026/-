"""
src/agent.py
LangChain-based Agent that orchestrates the full video production pipeline.

Pipeline:
  1. Script generation  → LLM writes narration script from user prompt
  2. Scene breakdown    → LLM splits script into shot descriptions
  3. Image generation   → ImageGenerator creates storyboard frames
  4. Video generation   → VideoGenerator animates each frame
  5. Audio synthesis    → AudioGenerator creates narration audio
  6. Subtitle creation  → SubtitleProcessor transcribes & formats
  7. Composition        → VideoCompositor assembles final video
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional

from openai import AsyncOpenAI

from src.generators.audio_gen import AudioGenerator
from src.generators.image_gen import ImageGenerator
from src.generators.video_gen import VideoGenerator
from src.processors.compositor import VideoCompositor
from src.processors.subtitle import SubtitleProcessor
from src.utils.config import settings
from src.utils.file_utils import make_output_path, safe_remove
from src.utils.logger import logger

Style = Literal["cinematic", "anime", "realistic", "cartoon", "documentary"]


@dataclass
class VideoResult:
    output_path: Path
    duration: float
    script: str
    scenes: List[str]
    temp_files: List[Path] = field(default_factory=list)

    def cleanup(self) -> None:
        for f in self.temp_files:
            safe_remove(f)


@dataclass
class AgentConfig:
    image_backend: str = "openai"
    video_backend: str = "kling"
    audio_backend: str = "edge"
    whisper_model: str = "base"
    voice: str = "zh-CN-XiaoxiaoNeural"
    clip_duration: int = 5
    style: Style = "cinematic"
    add_subtitles: bool = True
    add_bgm: bool = False


class VideoAgent:
    """
    High-level orchestrator. Example usage::

        agent = VideoAgent()
        result = await agent.create(
            prompt="一只熊猫在竹林中漫步，画面唯美",
            duration=15,
        )
        print(result.output_path)
    """

    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self.config = config or AgentConfig()
        self._llm = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._image_gen = ImageGenerator(backend=self.config.image_backend)  # type: ignore[arg-type]
        self._video_gen = VideoGenerator(backend=self.config.video_backend)  # type: ignore[arg-type]
        self._audio_gen = AudioGenerator(backend=self.config.audio_backend)  # type: ignore[arg-type]
        self._subtitle = SubtitleProcessor(model_size=self.config.whisper_model)
        self._compositor = VideoCompositor()

    # ── Public API ────────────────────────────────────────────────────────────

    async def create(
        self,
        prompt: str,
        *,
        duration: int = 15,
        style: Optional[Style] = None,
        voice: Optional[str] = None,
        subtitles: bool = True,
        bgm_path: Optional[Path] = None,
        output_name: Optional[str] = None,
    ) -> VideoResult:
        """
        Generate a complete video from a text prompt.

        Args:
            prompt:      Theme / topic of the video.
            duration:    Desired total length in seconds.
            style:       Visual style override.
            voice:       TTS voice override.
            subtitles:   Whether to embed auto-generated subtitles.
            bgm_path:    Optional background music file.
            output_name: Base name for the output file.

        Returns:
            VideoResult with output_path and metadata.
        """
        style = style or self.config.style
        voice = voice or self.config.voice
        n_clips = max(1, duration // self.config.clip_duration)
        temp_files: List[Path] = []

        logger.info(f"[Agent] Starting pipeline — {n_clips} clips, style={style}")

        # ── Step 1: Generate script ─────────────────────────────────────────
        script = await self._write_script(prompt, duration=duration, style=style)
        logger.info(f"[Agent] Script written ({len(script)} chars)")

        # ── Step 2: Break into scenes ───────────────────────────────────────
        scenes = await self._split_scenes(script, n_scenes=n_clips)
        logger.info(f"[Agent] {len(scenes)} scenes planned")

        # ── Step 3: Generate images (parallel) ─────────────────────────────
        image_tasks = [
            self._image_gen.generate(
                f"{scene}, {style} style, cinematic lighting",
                width=1792,
                height=1024,
            )
            for scene in scenes
        ]
        image_paths = list(await asyncio.gather(*image_tasks))
        temp_files.extend(image_paths)
        logger.info(f"[Agent] {len(image_paths)} frames generated")

        # ── Step 4: Animate frames → video clips ────────────────────────────
        clip_tasks = [
            self._video_gen.generate(
                scene,
                image_path=img,
                duration=self.config.clip_duration,
            )
            for scene, img in zip(scenes, image_paths)
        ]
        clip_paths = list(await asyncio.gather(*clip_tasks))
        temp_files.extend(clip_paths)

        # ── Step 5: Concatenate clips ────────────────────────────────────────
        merged = self._compositor.concatenate(clip_paths)
        temp_files.append(merged)

        # ── Step 6: Generate narration audio ────────────────────────────────
        audio_path = await self._audio_gen.generate(script, voice=voice)
        temp_files.append(audio_path)

        # ── Step 7: Mix audio ────────────────────────────────────────────────
        with_audio = self._compositor.mix_audio(merged, audio_path)
        temp_files.append(with_audio)

        # ── Step 8: Background music (optional) ─────────────────────────────
        current = with_audio
        if bgm_path and bgm_path.exists():
            current = self._compositor.add_bgm(with_audio, bgm_path)
            temp_files.append(current)

        # ── Step 9: Subtitles (optional) ─────────────────────────────────────
        if subtitles:
            srt = self._subtitle.transcribe(audio_path)
            current = self._subtitle.embed(current, srt)
            temp_files.append(current)

        # ── Step 10: Move to final output ────────────────────────────────────
        name = output_name or prompt[:30]
        final_path = make_output_path(name)
        import shutil
        shutil.move(str(current), str(final_path))

        logger.success(f"[Agent] Pipeline complete → {final_path}")
        return VideoResult(
            output_path=final_path,
            duration=float(n_clips * self.config.clip_duration),
            script=script,
            scenes=scenes,
            temp_files=[f for f in temp_files if f != current],
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _write_script(self, prompt: str, *, duration: int, style: str) -> str:
        system = (
            "你是一位专业的短视频脚本作家。"
            "请根据用户提供的主题，写一段适合配音的视频旁白脚本。"
            f"脚本时长约{duration}秒，风格为{style}。"
            "只输出旁白文本，不要包含分镜标注或演员指示。"
        )
        resp = await self._llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=500,
        )
        return resp.choices[0].message.content or ""

    async def _split_scenes(self, script: str, *, n_scenes: int) -> List[str]:
        system = (
            f"将以下视频旁白脚本分割为{n_scenes}个画面分镜描述。"
            "每个分镜描述应为1-2句画面场景描述（适合输入图像生成模型），用于生成对应画面。"
            "以JSON数组格式返回，每个元素为一个分镜描述字符串，不要包含其他内容。"
        )
        resp = await self._llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": script},
            ],
            temperature=0.5,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        import json
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        # Expect {"scenes": [...]} or top-level list
        if isinstance(data, list):
            scenes = data
        else:
            scenes = data.get("scenes") or list(data.values())[0]
        return scenes[:n_scenes]
