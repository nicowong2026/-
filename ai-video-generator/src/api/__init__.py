"""
src/api/__init__.py
FastAPI application factory export.
"""

from src.api.app import app, create_app

__all__ = ["app", "create_app"]
