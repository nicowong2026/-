# 🎬 AI Video Generator

<div align="center">

[![CI](https://github.com/your-username/ai-video-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/ai-video-generator/actions/workflows/ci.yml)
[![Lint](https://github.com/your-username/ai-video-generator/actions/workflows/lint.yml/badge.svg)](https://github.com/your-username/ai-video-generator/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/your-username/ai-video-generator/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/ai-video-generator)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-orange.svg)

**一个基于 AI 的全流程视频生成与制作工具包**

文本生成视频 · AI 配音 · 字幕自动生成 · 多模型后端 · 一键出片

[快速开始](docs/QUICKSTART.md) · [API 文档](docs/API.md) · [架构设计](docs/ARCHITECTURE.md) · [开发指南](docs/DEVELOPMENT.md) · [贡献指南](CONTRIBUTING.md)

</div>

---

## ✨ 功能特性

| 模块 | 能力 | 支持后端 |
|------|------|---------|
| 🖼️ **文生图** | 高质量 AI 图像生成 | DALL·E 3 / Stability SDXL / Flux(本地) |
| 🎬 **图生视频** | 将图像动态化为视频片段 | Kling AI / Runway Gen-3 / CogVideoX-5B |
| 🗣️ **AI 配音** | 多语言自然语音合成 | ElevenLabs / Azure TTS / Edge TTS(免费) / OpenAI |
| 📝 **字幕生成** | 自动识别并嵌入字幕 | Whisper Large-v3 / faster-whisper |
| ✂️ **视频合成** | 拼接、混音、转场、BGM | FFmpeg / MoviePy |
| 🤖 **Agent 调度** | 全流程自动编排 | LangChain + GPT-4o |
| 🌐 **REST API** | 异步任务接口 | FastAPI + Uvicorn |
| 💻 **CLI 工具** | 一行命令生成视频 | Typer |

---

## 🏗️ 项目结构

```
ai-video-generator/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # 多版本测试矩阵
│   │   ├── lint.yml             # 代码质量检查
│   │   ├── release.yml          # Tag 触发自动发布
│   │   └── dependency-review.yml
│   ├── ISSUE_TEMPLATE/          # Bug / Feature / Security 模板
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── dependabot.yml
├── src/
│   ├── generators/              # 多后端生成器
│   │   ├── image_gen.py
│   │   ├── video_gen.py
│   │   └── audio_gen.py
│   ├── processors/              # 后处理
│   │   ├── subtitle.py
│   │   └── compositor.py
│   ├── api/                     # FastAPI REST 服务
│   │   ├── app.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── utils/                   # 配置 / 日志 / 工具
│   ├── agent.py                 # LangChain Agent 编排器
│   └── cli.py                   # CLI 入口
├── tests/                       # pytest 测试套件
├── examples/                    # 使用示例
├── docs/                        # 文档
│   ├── QUICKSTART.md
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DEVELOPMENT.md
├── assets/                      # 静态资源（BGM、字体等）
├── .env.example                 # 环境变量模板
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE                      # MIT
├── Dockerfile
├── docker-compose.yml
├── MANIFEST.in
├── setup.cfg
├── pyproject.toml               # PEP 517 标准构建配置
└── requirements.txt
```

---

## 🚀 快速开始

> 完整安装说明见 [docs/QUICKSTART.md](docs/QUICKSTART.md)

### 环境要求

- Python 3.10+
- FFmpeg 6.0+（`brew install ffmpeg` / `apt install ffmpeg`）

### 安装

```bash
git clone https://github.com/your-username/ai-video-generator.git
cd ai-video-generator

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
cp .env.example .env        # 填入你的 API Keys
```

### 一行生成视频（CLI）

```bash
ai-video generate "夕阳下的大漠孤烟，驼铃声远，意境悠远" --duration 15
```

### Python 调用

```python
import asyncio
from src.agent import VideoAgent

async def main():
    agent = VideoAgent()
    result = await agent.create(
        prompt="春日傍晚，金黄余晖洒在宁静湖面，白鹭翻飞",
        duration=15,
        style="cinematic",
        subtitles=True,
    )
    print(result.output_path)  # output/春日傍晚_a1b2c3d4.mp4

asyncio.run(main())
```

### 启动 REST API

```bash
uvicorn src.api.app:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

---

## 🐳 Docker 部署

```bash
cp .env.example .env  # 先配置好 API Keys
docker-compose up -d

curl http://localhost:8000/health  # {"status":"ok"}
```

---

## 🧪 测试

```bash
pytest tests/ -v --cov=src
```

---

## 📖 AI 模型支持

<details>
<summary>图像生成后端</summary>

| 后端 | 模型 | 特点 |
|------|------|------|
| `openai` | DALL·E 3 | 质量高，中文 prompt 友好 |
| `stability` | Stable Diffusion XL | 可控性强，支持 negative prompt |
| `local` | Flux.1-dev / SDXL | 免费，需 GPU（VRAM 8GB+） |

</details>

<details>
<summary>视频生成后端</summary>

| 后端 | 模型 | 特点 |
|------|------|------|
| `kling` | Kling AI v1 | 中文支持好，画质稳定 |
| `runway` | Gen-3 Alpha Turbo | 动作流畅，国际主流 |
| `local` | CogVideoX-5B | 开源免费，需 A100/H100 |

</details>

<details>
<summary>语音合成后端</summary>

| 后端 | 特点 | 费用 |
|------|------|------|
| `edge` | Microsoft Edge TTS，中文支持佳 | 完全免费 |
| `openai` | 自然流畅，多语言 | 按字符计费 |
| `elevenlabs` | 音色克隆，情感丰富 | 免费额度 + 付费 |
| `azure` | 企业级，稳定 | 按字符计费 |

</details>

---

## 🤝 贡献

欢迎任何形式的贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
git checkout -b feat/your-feature
# 开发...
git commit -m "feat: add your feature"
git push origin feat/your-feature
# 提交 Pull Request
```

---

## 📄 许可证

[MIT License](LICENSE) © 2026 AI Video Generator Contributors

---

<div align="center">
<sub>Built with ❤️ by AI Builders · <a href="https://github.com/your-username/ai-video-generator/discussions">Join the Discussion</a></sub>
</div>
