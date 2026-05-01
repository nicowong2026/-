"""
src/utils/logger.py
Structured logging powered by Loguru with Rich console output.
"""

import sys

from loguru import logger

from src.utils.config import settings

# Remove default handler
logger.remove()

# Console handler
logger.add(
    sys.stderr,
    level=settings.log_level,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    colorize=True,
)

# File handler (rotated daily, kept 7 days)
logger.add(
    "logs/ai_video_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    compression="gz",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

__all__ = ["logger"]
