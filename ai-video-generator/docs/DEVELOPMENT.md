# Developer Guide

## Development Setup

```bash
git clone https://github.com/your-username/ai-video-generator.git
cd ai-video-generator
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Project Layout

```
src/
├── __init__.py           # Package metadata (__version__)
├── agent.py              # VideoAgent — top-level orchestrator
├── cli.py                # Typer CLI entry point
├── generators/
│   ├── image_gen.py      # ImageGenerator (openai/stability/local)
│   ├── video_gen.py      # VideoGenerator (kling/runway/local)
│   └── audio_gen.py      # AudioGenerator (openai/elevenlabs/edge/azure)
├── processors/
│   ├── subtitle.py       # Whisper transcription + FFmpeg embed
│   └── compositor.py     # FFmpeg concat, audio mix, BGM
├── api/
│   ├── app.py            # FastAPI factory
│   ├── routes.py         # Route handlers
│   └── schemas.py        # Pydantic models
└── utils/
    ├── config.py          # pydantic-settings config
    ├── logger.py          # Loguru logger
    └── file_utils.py      # File path helpers
```

## Running Tests

```bash
# All tests with coverage
pytest tests/ -v

# Single module
pytest tests/test_image_gen.py -v

# With live API calls (set env vars first)
pytest tests/ -v -m integration
```

## Adding a New Video Backend

1. Add backend name to the `Backend` type alias in `src/generators/video_gen.py`
2. Implement `_generate_<name>` async method in `VideoGenerator`
3. Wire it in the `generate()` dispatch block
4. Add tests in `tests/test_video_gen.py`
5. Update `README.md` under "Supported AI Models"
6. Add a `CHANGELOG.md` entry

## Code Style

```bash
black src/ tests/          # Format
ruff check --fix src/      # Lint + auto-fix
mypy src/                  # Type check
bandit -r src/             # Security scan
```

## Making a Release

1. Update `CHANGELOG.md` — move items from `[Unreleased]` to a new version section
2. Bump version in `pyproject.toml`
3. Commit: `git commit -m "chore: release v0.x.0"`
4. Tag: `git tag v0.x.0`
5. Push: `git push origin main --tags`
6. GitHub Actions will automatically create a Release and attach build artifacts

## Environment Variables Reference

See [`.env.example`](../.env.example) for the full list with descriptions.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | — | GPT-4o for script generation |
| `KLING_API_KEY` | For Kling | — | Kling AI video generation |
| `STABILITY_API_KEY` | For SDXL | — | Stability AI image generation |
| `ELEVENLABS_API_KEY` | For ElevenLabs | — | High-quality TTS |
| `RUNWAY_API_KEY` | For Runway | — | Runway video generation |
| `OUTPUT_DIR` | ❌ | `./output` | Output file directory |
| `LOG_LEVEL` | ❌ | `INFO` | Logging verbosity |
