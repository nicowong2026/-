"""
src/__init__.py
AI Video Generator — public package surface.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ai-video-generator")
except PackageNotFoundError:
    __version__ = "0.1.0-dev"

__all__ = ["__version__"]
