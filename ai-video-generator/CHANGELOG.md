# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Pika Labs video backend
- Background music library integration
- Web UI (React + Next.js)
- Celery + Redis async task queue
- Video watermark / branding overlay

---

## [0.1.0] - 2026-05-01

### Added
- **ImageGenerator**: DALL·E 3, Stability AI SDXL, local Diffusers backends
- **VideoGenerator**: Kling AI v1, Runway Gen-3 Alpha, CogVideoX-5B backends
- **AudioGenerator**: OpenAI TTS, ElevenLabs multilingual v2, Edge TTS, Azure TTS
- **SubtitleProcessor**: Whisper transcription + FFmpeg subtitle embedding
- **VideoCompositor**: FFmpeg concatenation, audio mixing, BGM overlay
- **VideoAgent**: LangChain-based full-pipeline orchestrator
- **REST API**: FastAPI async endpoints with background task queue
- **CLI**: Typer-based command-line interface
- Docker / docker-compose support
- GitHub Actions CI/CD (test matrix + Docker build)

[Unreleased]: https://github.com/your-username/ai-video-generator/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-username/ai-video-generator/releases/tag/v0.1.0
