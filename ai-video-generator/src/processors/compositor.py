"""
src/processors/compositor.py
Video composition, splicing, transitions, and audio mixing via FFmpeg/MoviePy.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from src.utils.file_utils import make_temp_path
from src.utils.logger import logger


class VideoCompositor:
    """Combine multiple video clips and audio tracks into a single output."""

    def concatenate(
        self,
        clips: List[Path],
        *,
        output_path: Optional[Path] = None,
        transition: str = "none",
        transition_duration: float = 0.5,
    ) -> Path:
        """
        Concatenate a list of video clips.

        Args:
            clips:               Ordered list of video file paths.
            output_path:         Output file path.
            transition:          'none' | 'fade' | 'dissolve'
            transition_duration: Transition length in seconds.

        Returns:
            Path to the merged video.
        """
        import ffmpeg

        output_path = output_path or make_temp_path(".mp4")
        logger.info(f"[Compositor] Concatenating {len(clips)} clips…")

        if transition == "none":
            # Simple concat demuxer
            list_path = make_temp_path(".txt")
            list_path.write_text(
                "\n".join(f"file '{p.resolve()}'" for p in clips), encoding="utf-8"
            )
            try:
                (
                    ffmpeg.input(str(list_path), format="concat", safe=0)
                    .output(str(output_path), c="copy")
                    .overwrite_output()
                    .run(quiet=True)
                )
            finally:
                list_path.unlink(missing_ok=True)
        else:
            # Use MoviePy for transitions
            self._concatenate_moviepy(clips, output_path, transition, transition_duration)

        logger.success(f"[Compositor] Merged → {output_path}")
        return output_path

    def mix_audio(
        self,
        video_path: Path,
        audio_path: Path,
        *,
        output_path: Optional[Path] = None,
        video_volume: float = 0.3,
        audio_volume: float = 1.0,
        loop_audio: bool = False,
    ) -> Path:
        """
        Replace or overlay audio track on a video.

        Args:
            video_path:   Source video.
            audio_path:   Narration / music audio.
            output_path:  Destination path.
            video_volume: Original video audio volume (0 = mute).
            audio_volume: New audio track volume.
            loop_audio:   Loop audio if shorter than video.

        Returns:
            Path to the mixed video.
        """
        import ffmpeg

        output_path = output_path or make_temp_path(".mp4")
        logger.info("[Compositor] Mixing audio…")

        video_stream = ffmpeg.input(str(video_path))
        audio_stream = ffmpeg.input(str(audio_path))

        if loop_audio:
            audio_stream = ffmpeg.input(str(audio_path), stream_loop=-1)

        mixed = ffmpeg.filter(
            [video_stream.audio.filter("volume", video_volume),
             audio_stream.filter("volume", audio_volume)],
            "amix",
            inputs=2,
            duration="first",
        )

        (
            ffmpeg.output(
                video_stream.video,
                mixed,
                str(output_path),
                vcodec="copy",
                acodec="aac",
                shortest=None,
            )
            .overwrite_output()
            .run(quiet=True)
        )

        logger.success(f"[Compositor] Mixed → {output_path}")
        return output_path

    def add_bgm(
        self,
        video_path: Path,
        bgm_path: Path,
        *,
        bgm_volume: float = 0.15,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Overlay background music at low volume."""
        return self.mix_audio(
            video_path,
            bgm_path,
            output_path=output_path,
            video_volume=1.0,
            audio_volume=bgm_volume,
            loop_audio=True,
        )

    def _concatenate_moviepy(
        self,
        clips: List[Path],
        output_path: Path,
        transition: str,
        transition_duration: float,
    ) -> None:
        from moviepy.editor import VideoFileClip, concatenate_videoclips

        loaded = [VideoFileClip(str(c)) for c in clips]
        method = "compose" if transition in ("fade", "dissolve") else "chain"
        final = concatenate_videoclips(loaded, method=method)
        final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)
        for c in loaded:
            c.close()
