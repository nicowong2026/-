"""
src/generators/audio_gen.py
AI speech synthesis (TTS) with multi-backend support.

Supported backends:
- openai     : OpenAI TTS-1 / TTS-1-HD
- elevenlabs : ElevenLabs multilingual v2 (best quality)
- edge       : Microsoft Edge TTS (free, no API key)
- azure      : Azure Cognitive Speech (enterprise)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import settings
from src.utils.file_utils import make_temp_path
from src.utils.logger import logger

Backend = Literal["openai", "elevenlabs", "edge", "azure"]


class AudioGenerator:
    """Convert text to speech and save as MP3/WAV."""

    def __init__(self, backend: Backend = "edge") -> None:
        self.backend = backend

    async def generate(
        self,
        text: str,
        *,
        voice: str = "zh-CN-XiaoxiaoNeural",
        speed: float = 1.0,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Synthesise *text* into speech.

        Args:
            text:        Input text (max ~5000 chars depending on backend).
            voice:       Voice identifier (backend-specific).
            speed:       Playback speed multiplier (0.5–2.0).
            output_path: Save location; auto-generated if None.

        Returns:
            Path to the generated audio file.
        """
        logger.info(f"[AudioGen/{self.backend}] TTS: {text[:60]}…")
        output_path = output_path or make_temp_path(".mp3")

        if self.backend == "openai":
            await self._tts_openai(text, voice=voice, speed=speed, output_path=output_path)
        elif self.backend == "elevenlabs":
            await self._tts_elevenlabs(text, voice_id=voice, output_path=output_path)
        elif self.backend == "edge":
            await self._tts_edge(text, voice=voice, rate=speed, output_path=output_path)
        elif self.backend == "azure":
            await self._tts_azure(text, voice=voice, output_path=output_path)
        else:
            raise ValueError(f"Unknown TTS backend: {self.backend}")

        logger.success(f"[AudioGen] Saved → {output_path}")
        return output_path

    # ── Backends ──────────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8))
    async def _tts_openai(
        self, text: str, *, voice: str, speed: float, output_path: Path
    ) -> None:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        valid_voices = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
        oai_voice = voice if voice in valid_voices else "nova"
        async with client.audio.speech.with_streaming_response.create(
            model=settings.openai_tts_model,
            voice=oai_voice,  # type: ignore[arg-type]
            input=text,
            speed=speed,
            response_format="mp3",
        ) as response:
            output_path.write_bytes(await response.read())

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8))
    async def _tts_elevenlabs(
        self, text: str, *, voice_id: str, output_path: Path
    ) -> None:
        import httpx

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {"xi-api-key": settings.elevenlabs_api_key, "Content-Type": "application/json"}
        body = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)

    async def _tts_edge(
        self, text: str, *, voice: str, rate: float, output_path: Path
    ) -> None:
        import edge_tts

        rate_str = f"+{int((rate - 1) * 100)}%" if rate >= 1 else f"{int((rate - 1) * 100)}%"
        communicate = edge_tts.Communicate(text, voice, rate=rate_str)
        await communicate.save(str(output_path))

    async def _tts_azure(
        self, text: str, *, voice: str, output_path: Path
    ) -> None:
        import azure.cognitiveservices.speech as speechsdk

        speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region,
        )
        speech_config.speech_synthesis_voice_name = voice
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )
        result = synthesizer.speak_text_async(text).get()
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            raise RuntimeError(f"Azure TTS failed: {result.cancellation_details}")
