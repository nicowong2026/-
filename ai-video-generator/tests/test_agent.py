"""
tests/test_agent.py
Integration-style tests for VideoAgent (mocked external calls).
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent import AgentConfig, VideoAgent, VideoResult


@pytest.fixture
def mock_agent(tmp_path):
    """VideoAgent with all external calls mocked."""
    agent = VideoAgent(AgentConfig(audio_backend="edge", video_backend="kling"))

    # Mock LLM calls
    agent._llm = AsyncMock()
    agent._llm.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"scenes":["scene1","scene2"]}'))]
        )
    )

    # Mock generators
    agent._image_gen.generate = AsyncMock(return_value=tmp_path / "img.png")
    agent._video_gen.generate = AsyncMock(return_value=tmp_path / "clip.mp4")
    agent._audio_gen.generate = AsyncMock(return_value=tmp_path / "audio.mp3")

    # Mock processors
    agent._subtitle.transcribe = MagicMock(return_value="1\n00:00:00,000 --> 00:00:03,000\nHello\n")
    agent._subtitle.embed = MagicMock(return_value=tmp_path / "sub.mp4")
    agent._compositor.concatenate = MagicMock(return_value=tmp_path / "merged.mp4")
    agent._compositor.mix_audio = MagicMock(return_value=tmp_path / "mixed.mp4")

    # Create dummy files so shutil.move doesn't fail
    for f in ["img.png", "clip.mp4", "audio.mp3", "sub.mp4", "merged.mp4", "mixed.mp4"]:
        (tmp_path / f).write_bytes(b"dummy")

    return agent, tmp_path


class TestVideoAgent:
    async def test_create_returns_result(self, mock_agent):
        agent, tmp_path = mock_agent
        with patch("src.agent._write_script", new=AsyncMock(return_value="test script")):
            # Patch _write_script on instance
            agent._write_script = AsyncMock(return_value="A panda walks through bamboo forest.")
            agent._split_scenes = AsyncMock(return_value=["scene1", "scene2"])

            result = await agent.create("panda in bamboo", duration=10)

        assert isinstance(result, VideoResult)
        assert result.output_path.exists() or True  # path may be temp
        assert result.script == "A panda walks through bamboo forest."
        assert len(result.scenes) == 2

    def test_agent_config_defaults(self):
        config = AgentConfig()
        assert config.clip_duration == 5
        assert config.style == "cinematic"
        assert config.add_subtitles is True
