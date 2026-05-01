# Quick Start Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| FFmpeg | 6.0+ | `brew install ffmpeg` / `apt install ffmpeg` |
| Git | any | [git-scm.com](https://git-scm.com/) |
| CUDA (optional) | 11.8+ | For local model inference |

---

## Step 1 — Clone & Install

```bash
git clone https://github.com/your-username/ai-video-generator.git
cd ai-video-generator

# Create isolated virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install core dependencies
pip install -e .

# Or install with dev tools
pip install -e ".[dev]"

# Or install with GPU support (requires CUDA)
pip install -e ".[gpu]"
```

## Step 2 — Configure API Keys

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```dotenv
OPENAI_API_KEY=sk-...        # Required for script generation
KLING_API_KEY=...            # Required for video generation (or use 'runway')
KLING_API_SECRET=...
```

> 💡 **Tip**: Use `edge` as `audio_backend` — it's completely free and requires no API key.

## Step 3 — Generate Your First Video

### Option A: Command Line

```bash
ai-video generate "夕阳下的大漠孤烟，驼铃声远，意境悠远" --duration 15 --style cinematic
```

### Option B: Python API

```python
import asyncio
from src.agent import VideoAgent

async def main():
    agent = VideoAgent()
    result = await agent.create(
        prompt="夕阳下的大漠孤烟，驼铃声远，意境悠远",
        duration=15,
        style="cinematic",
        subtitles=True,
    )
    print(f"Video saved to: {result.output_path}")

asyncio.run(main())
```

### Option C: REST API

```bash
# Start server
uvicorn src.api.app:app --port 8000

# Submit job
curl -X POST http://localhost:8000/v1/videos \
  -H "Content-Type: application/json" \
  -d '{"prompt": "夕阳大漠", "duration": 15}'

# Poll status
curl http://localhost:8000/v1/videos/{task_id}
```

## Step 4 — Docker (Recommended for Production)

```bash
# Copy and configure .env first!
cp .env.example .env

docker-compose up -d

# Check health
curl http://localhost:8000/health
```

---

## Common Issues

### `ffmpeg not found`
Install FFmpeg and ensure it's on your PATH:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install -y ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

### `OPENAI_API_KEY not set`
Make sure you've copied `.env.example` to `.env` and filled in your key.

### Out of memory with local models
Use a cloud backend instead:
```python
from src.agent import AgentConfig
config = AgentConfig(image_backend="openai", video_backend="kling")
```

---

## Next Steps

- 📖 [API Reference](API.md)
- 🏗️ [Architecture Overview](ARCHITECTURE.md)
- 🤝 [Contributing Guide](../CONTRIBUTING.md)
