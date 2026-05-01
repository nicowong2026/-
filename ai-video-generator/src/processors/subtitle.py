"""
src/processors/subtitle.py
Automatic subtitle generation via OpenAI Whisper and SRT/ASS embedding.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import List, Optional

from src.utils.config import settings
from src.utils.file_utils import make_temp_path
from src.utils.logger import logger


def _fmt_srt_time(seconds: float) -> str:
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((seconds - int(seconds)) * 1000)
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"


def segments_to_srt(segments: list) -> str:
    """Convert Whisper transcript segments to SRT format."""
    lines: List[str] = []
    for i, seg in enumerate(segments, start=1):
        start = _fmt_srt_time(seg["start"])
        end = _fmt_srt_time(seg["end"])
        text = seg["text"].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


class SubtitleProcessor:
    """Transcribe audio and embed subtitles into video."""

    def __init__(self, model_size: str = "base") -> None:
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                import whisper
                logger.info(f"[Subtitle] Loading Whisper {self.model_size}…")
                self._model = whisper.load_model(self.model_size)
            except ImportError as exc:
                raise ImportError("pip install openai-whisper") from exc
        return self._model

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to SRT subtitle string.

        Args:
            audio_path: Path to .mp3 / .wav / .m4a
            language:   Optional language hint (e.g. 'zh', 'en')

        Returns:
            SRT-formatted subtitle text.
        """
        model = self._load_model()
        logger.info(f"[Subtitle] Transcribing {audio_path.name}…")
        options = {"task": "transcribe"}
        if language:
            options["language"] = language
        result = model.transcribe(str(audio_path), **options)
        srt = segments_to_srt(result["segments"])
        logger.success(f"[Subtitle] Transcribed {len(result['segments'])} segments")
        return srt

    def embed(
        self,
        video_path: Path,
        srt_content: str,
        *,
        output_path: Optional[Path] = None,
        font_size: int = 22,
        font_color: str = "white",
        position: str = "bottom",
    ) -> Path:
        """
        Burn subtitles into video using FFmpeg.

        Args:
            video_path:  Source video.
            srt_content: SRT text.
            output_path: Destination video path.
            font_size:   Subtitle font size.
            font_color:  Subtitle colour (FFmpeg colour name).
            position:    'bottom' or 'top'.

        Returns:
            Path to the video with embedded subtitles.
        """
        import ffmpeg

        # Write SRT to temp file
        srt_path = make_temp_path(".srt")
        srt_path.write_text(srt_content, encoding="utf-8")

        output_path = output_path or make_temp_path(".mp4")
        y_pos = "h-th-20" if position == "bottom" else "20"

        vf_filter = (
            f"subtitles={srt_path}:force_style="
            f"'FontSize={font_size},PrimaryColour=&H{_color_to_hex(font_color)}&,"
            f"Alignment=2,MarginV=30'"
        )

        try:
            (
                ffmpeg.input(str(video_path))
                .output(
                    str(output_path),
                    vf=vf_filter,
                    codec="libx264",
                    audio_codec="aac",
                )
                .overwrite_output()
                .run(quiet=True)
            )
        finally:
            srt_path.unlink(missing_ok=True)

        logger.success(f"[Subtitle] Embedded → {output_path}")
        return output_path


def _color_to_hex(name: str) -> str:
    """Convert common colour names to BGR hex for FFmpeg ASS style."""
    mapping = {
        "white": "00FFFFFF",
        "yellow": "0000FFFF",
        "black": "00000000",
        "red": "000000FF",
    }
    return mapping.get(name.lower(), "00FFFFFF")
