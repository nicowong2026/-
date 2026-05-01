"""
examples/basic_usage.py
Minimal example: generate a 15-second video from a text prompt.

Prerequisites:
  1. pip install -e ".[dev]"
  2. cp .env.example .env  # fill in your API keys
  3. python examples/basic_usage.py
"""

import asyncio
from src.agent import AgentConfig, VideoAgent


async def main():
    # Choose your backends — all free/low-cost options shown here
    config = AgentConfig(
        image_backend="openai",      # DALL·E 3
        video_backend="kling",       # Kling AI
        audio_backend="edge",        # Microsoft Edge TTS (free)
        whisper_model="base",        # Faster, less accurate
        voice="zh-CN-XiaoxiaoNeural",
        clip_duration=5,
        style="cinematic",
        add_subtitles=True,
    )

    agent = VideoAgent(config)

    print("🎬 Generating AI video…")
    result = await agent.create(
        prompt="春日傍晚，金黄的余晖洒在宁静的湖面上，远处山峦叠嶂，白鹭翻飞",
        duration=15,
    )

    print(f"✅ Done! Output: {result.output_path}")
    print(f"\n📝 Script:\n{result.script}")
    print(f"\n🎞️  Scenes ({len(result.scenes)}):")
    for i, scene in enumerate(result.scenes, 1):
        print(f"  {i}. {scene}")

    # Optionally clean up temp files
    result.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
