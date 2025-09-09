from __future__ import annotations

import glob
import re
from pathlib import Path
from typing import TYPE_CHECKING

import logistro

if TYPE_CHECKING:
    from . import _fig_tools

_logger = logistro.getLogger(__name__)


def _next_filename(path: Path | str, prefix: str, ext: str) -> str:
    path = path if isinstance(path, Path) else Path(path)
    default = 1 if (path / f"{prefix}.{ext}").exists() else 0
    re_number = re.compile(
        r"^" + re.escape(prefix) + r"\-(\d+)\." + re.escape(ext) + r"$",
    )
    escaped_prefix = glob.escape(prefix)
    escaped_ext = glob.escape(ext)
    numbers = [
        int(match.group(1))
        for name in path.glob(f"{escaped_prefix}-*.{escaped_ext}")
        if (match := re_number.match(Path(name).name))
    ]
    n = max(numbers, default=default) + 1
    return f"{prefix}.{ext}" if n == 1 else f"{prefix}-{n}.{ext}"


def determine_path(
    path: Path | str | None,
    fig: dict,
    ext: _fig_tools.FormatString,
) -> Path:
    path = Path(path) if path else Path()

    if not path.suffix or path.is_dir():  # they gave us a directory
        if not path.is_dir():
            raise ValueError(f"Directory {path} not found. Please create it.")
        directory = path
        _logger.debug("Looking for title")
        prefix = fig.get("layout", {}).get("title", {}).get("text", "fig")
        prefix = re.sub(r"[ \-]", "_", prefix)
        prefix = re.sub(r"[^a-zA-Z0-9_]", "", prefix)
        prefix = prefix or "fig"
        _logger.debug(f"Found: {prefix}")
        name = _next_filename(directory, prefix, ext)
        full_path = directory / name
    else:  # we have full path, supposedly
        full_path = path
        if not full_path.parent.is_dir():
            raise RuntimeError(
                f"Cannot reach path {path.parent}. Are all directories created?",
            )
    return full_path
