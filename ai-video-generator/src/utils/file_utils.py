"""
src/utils/file_utils.py
Common file and path utilities.
"""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path
from typing import Optional

from src.utils.config import settings
from src.utils.logger import logger


def make_temp_path(suffix: str = ".tmp") -> Path:
    """Return a unique temp file path inside the configured temp dir."""
    return settings.temp_dir / f"{uuid.uuid4().hex}{suffix}"


def make_output_path(name: str, ext: str = ".mp4") -> Path:
    """Return a unique output file path inside the configured output dir."""
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    uid = uuid.uuid4().hex[:8]
    return settings.output_dir / f"{safe_name}_{uid}{ext}"


def file_hash(path: Path, algo: str = "sha256") -> str:
    """Compute hex digest of a file."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_remove(path: Optional[Path]) -> None:
    """Delete a file without raising if it doesn't exist."""
    if path and path.exists():
        try:
            path.unlink()
            logger.debug(f"Removed temp file: {path}")
        except OSError as exc:
            logger.warning(f"Could not remove {path}: {exc}")


def safe_move(src: Path, dst: Path) -> Path:
    """Move a file, creating destination directories as needed."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return dst
