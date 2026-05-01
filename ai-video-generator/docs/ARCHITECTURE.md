# Architecture Overview

## System Design

```
User Input (prompt)
       │
       ▼
┌─────────────────┐
│   VideoAgent    │  ← LangChain orchestrator
│  (src/agent.py) │
└────────┬────────┘
         │
    ┌────┴────┐
    │  LLM    │  GPT-4o: script + scene breakdown
    └────┬────┘
         │
  ┌──────▼──────┐
  │  Generators │
  │─────────────│
  │ ImageGen    │  DALL·E 3 / SDXL / local
  │ VideoGen    │  Kling / Runway / CogVideoX
  │ AudioGen    │  Edge TTS / ElevenLabs / OpenAI
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Processors  │
  │─────────────│
  │ Compositor  │  FFmpeg concat + audio mix
  │ Subtitle    │  Whisper → SRT → FFmpeg embed
  └──────┬──────┘
         │
    ┌────▼────┐
    │ Output  │  final .mp4
    └─────────┘
```

## Key Design Decisions

### 1. Async-first
All external API calls are `async` to maximise throughput when generating
multiple clips in parallel (Step 3 & 4 of the pipeline).

### 2. Pluggable Backends
Each generator accepts a `backend` parameter so users can swap providers
without changing orchestration logic. Adding a new backend requires
implementing only one private method.

### 3. Stateless API
The REST API stores task state in a simple in-memory dict.
For production, swap this with Redis + a proper task queue (Celery/ARQ).

### 4. Temp File Lifecycle
All intermediate files (frames, clips, audio) are created with unique UUIDs
in `tmp/`. `VideoResult.cleanup()` removes them after the caller is done.
