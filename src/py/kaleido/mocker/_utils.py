from __future__ import annotations

import itertools
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import logistro
import orjson

from ._args import args

if TYPE_CHECKING:
    ...

_logger = logistro.getLogger(__name__)


def get_jsons_in_paths(path: str | Path) -> list[Path]:
    # Work with Paths and directories
    path = Path(path) if isinstance(path, str) else path

    if path.is_dir():
        _logger.info(f"Input is path {path}")
        return list(path.glob("*.json"))
    elif path.is_file():
        _logger.info(f"Input is file {path}")
        return [path]
    else:
        raise TypeError("--input must be file or directory")


class Param(TypedDict):
    name: str
    opts: dict[str, int | float]


# maybe don't have this do params and figures
def load_figures_from_paths(paths: list[Path]):
    # Set json
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"Path {path} is not a file.")

        with path.open(encoding="utf-8") as file:
            figure = orjson.loads(file.read())
            for f, w, h, s in itertools.product(  # all combos
                args.format,
                args.width,
                args.height,
                args.scale,
            ):
                name = (
                    f"{path.stem}.{args.format}"
                    if not args.parameterize
                    else f"{path.stem!s}-{w!s}x{h!s}@{s!s}.{f!s}"
                )
                opts = {
                    "scale": s,
                    "width": w,
                    "height": h,
                }
                yield {
                    "fig": figure,
                    "path": str(Path(args.output) / name),
                    "opts": opts,
                }
