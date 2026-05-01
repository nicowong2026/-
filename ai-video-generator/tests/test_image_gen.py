"""
tests/test_image_gen.py
Unit tests for the ImageGenerator module.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.generators.image_gen import ImageGenerator


@pytest.fixture
def image_gen_openai():
    return ImageGenerator(backend="openai")


@pytest.fixture
def image_gen_stability():
    return ImageGenerator(backend="stability")


class TestImageGenerator:
    def test_init_default_backend(self):
        gen = ImageGenerator()
        assert gen.backend == "openai"

    def test_init_custom_backend(self):
        gen = ImageGenerator(backend="stability")
        assert gen.backend == "stability"

    def test_invalid_backend_raises(self):
        gen = ImageGenerator(backend="invalid")  # type: ignore
        with pytest.raises(ValueError, match="Unknown backend"):
            asyncio.run(gen.generate("test"))

    @patch("src.generators.image_gen.AsyncOpenAI")
    async def test_generate_openai_calls_api(self, mock_openai_cls, tmp_path):
        """OpenAI backend should call images.generate and write bytes."""
        import base64

        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json=base64.b64encode(fake_png).decode())]

        mock_client = AsyncMock()
        mock_client.images.generate = AsyncMock(return_value=mock_response)
        mock_openai_cls.return_value = mock_client

        gen = ImageGenerator(backend="openai")
        output = tmp_path / "test.png"
        result = await gen.generate("a panda in bamboo", output_path=output)

        assert result == output
        assert output.exists()
        assert output.read_bytes() == fake_png
        mock_client.images.generate.assert_called_once()

    async def test_generate_creates_file(self, image_gen_openai, tmp_path):
        """generate() should return an existing Path."""
        output = tmp_path / "out.png"
        with patch.object(image_gen_openai, "_generate_openai", new=AsyncMock()) as mock_fn:
            mock_fn.side_effect = lambda prompt, out, **kw: out.write_bytes(b"fake")
            result = await image_gen_openai.generate("test prompt", output_path=output)
        assert result.exists()
