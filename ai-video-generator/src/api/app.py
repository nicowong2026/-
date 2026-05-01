"""
src/api/app.py
FastAPI application factory.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.utils.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Video Generator API",
        description="Full-pipeline AI video generation: text → script → images → video → audio → subtitles",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
