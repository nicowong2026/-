"""
src/cli.py
Command-line interface powered by Typer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(name="ai-video", help="AI Video Generator CLI", add_completion=False)
console = Console()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Video theme / topic"),
    duration: int = typer.Option(15, "--duration", "-d", help="Target length in seconds"),
    style: str = typer.Option("cinematic", "--style", "-s", help="Visual style"),
    voice: str = typer.Option("zh-CN-XiaoxiaoNeural", "--voice", "-v", help="TTS voice"),
    no_subtitles: bool = typer.Option(False, "--no-subtitles", help="Skip subtitle generation"),
    image_backend: str = typer.Option("openai", "--image-backend", help="Image gen backend"),
    video_backend: str = typer.Option("kling", "--video-backend", help="Video gen backend"),
    audio_backend: str = typer.Option("edge", "--audio-backend", help="TTS backend"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Generate a video from a text prompt."""
    import asyncio

    from src.agent import AgentConfig, VideoAgent

    config = AgentConfig(
        image_backend=image_backend,
        video_backend=video_backend,
        audio_backend=audio_backend,
        style=style,  # type: ignore[arg-type]
        add_subtitles=not no_subtitles,
    )
    agent = VideoAgent(config)

    console.print(f"[bold cyan]🎬 AI Video Generator[/bold cyan]")
    console.print(f"Prompt: [italic]{prompt}[/italic]")
    console.print(f"Duration: {duration}s | Style: {style} | Voice: {voice}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating video pipeline…", total=None)
        result = asyncio.run(
            agent.create(
                prompt,
                duration=duration,
                style=style,  # type: ignore[arg-type]
                voice=voice,
                subtitles=not no_subtitles,
                output_name=output.stem if output else None,
            )
        )
        progress.update(task, description="Done!")

    console.print(f"\n✅ Video saved to: [green]{result.output_path}[/green]")
    console.print(f"Script preview: {result.script[:120]}…")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Start the REST API server."""
    import uvicorn

    uvicorn.run("src.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
