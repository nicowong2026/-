# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication is required for local deployment.
For production, add an `Authorization: Bearer <token>` header.

---

## Endpoints

### `GET /health`

Health check.

**Response**
```json
{"status": "ok", "version": "0.1.0"}
```

---

### `POST /v1/videos`

Submit a video generation task.

**Request Body**
```json
{
  "prompt": "一只熊猫在竹林中漫步",
  "duration": 15,
  "style": "cinematic",
  "voice": "zh-CN-XiaoxiaoNeural",
  "subtitles": true,
  "image_backend": "openai",
  "video_backend": "kling",
  "audio_backend": "edge"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | string | required | Video theme |
| `duration` | int | 15 | Total length (seconds) |
| `style` | string | cinematic | cinematic / anime / realistic / cartoon / documentary |
| `voice` | string | zh-CN-XiaoxiaoNeural | TTS voice ID |
| `subtitles` | bool | true | Auto-generate subtitles |
| `image_backend` | string | openai | openai / stability / local |
| `video_backend` | string | kling | kling / runway / local |
| `audio_backend` | string | edge | openai / elevenlabs / edge / azure |

**Response** `202 Accepted`
```json
{
  "task_id": "a1b2c3d4...",
  "status": "pending",
  "message": "Task submitted successfully"
}
```

---

### `GET /v1/videos/{task_id}`

Poll task status.

**Response**
```json
{
  "task_id": "a1b2c3d4...",
  "status": "completed",
  "progress": 1.0,
  "output_url": "/v1/download/a1b2c3d4...",
  "script": "春日傍晚，金黄的余晖…",
  "scenes": ["Scene 1 desc", "Scene 2 desc"]
}
```

Status values: `pending` → `running` → `completed` | `failed`

---

### `GET /v1/download/{task_id}`

Download the generated MP4 file.

**Response**: `video/mp4` binary stream

---

## Swagger UI

Interactive API docs are available at: `http://localhost:8000/docs`
