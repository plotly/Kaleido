from __future__ import annotations

import json
from pathlib import Path


def get_json_paths(path: str | Path) -> list[Path]:
    # Work with Paths and directories
    path = Path(path) if isinstance(path, str) else path

    if path.is_dir():
        return [ path / a for a in path.glob("*.json") ]
    else:
        return [ path ]

def load_figure_from_file(path: Path):
    path = Path(path) if isinstance(path, str) else path
    # Set json
    if path.is_file():
        with path.open() as file:
            figure = json.load(file)
    else:
        raise RuntimeError(f"Path {path} is not a file.")
    return figure, path.stem
