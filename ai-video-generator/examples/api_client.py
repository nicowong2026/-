"""
examples/api_client.py
Example of calling the REST API programmatically.

Run server first: uvicorn src.api.app:app --port 8000
"""

import asyncio
import time
import httpx


API_BASE = "http://localhost:8000/v1"


async def generate_video(prompt: str, duration: int = 15) -> str:
    async with httpx.AsyncClient(timeout=600) as client:
        # 1. Submit task
        resp = await client.post(
            f"{API_BASE}/videos",
            json={
                "prompt": prompt,
                "duration": duration,
                "style": "cinematic",
                "subtitles": True,
                "audio_backend": "edge",
            },
        )
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        print(f"Task submitted: {task_id}")

        # 2. Poll until done
        while True:
            status_resp = await client.get(f"{API_BASE}/videos/{task_id}")
            status_resp.raise_for_status()
            data = status_resp.json()
            print(f"  Status: {data['status']} ({data['progress']*100:.0f}%)")

            if data["status"] == "completed":
                print(f"\n✅ Done! Download: {API_BASE}/download/{task_id}")
                return task_id
            elif data["status"] == "failed":
                raise RuntimeError(f"Task failed: {data.get('error')}")

            await asyncio.sleep(5)


if __name__ == "__main__":
    task_id = asyncio.run(
        generate_video("夕阳下海边奔跑的小女孩，画面温馨治愈", duration=10)
    )
    print(f"\nDownload URL: {API_BASE}/download/{task_id}")
