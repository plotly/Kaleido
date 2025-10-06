from __future__ import annotations

import itertools
import pickle
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import logistro
import orjson

try:
    import zstandard as zstd

    dctx = zstd.ZstdDecompressor()
except ImportError:
    dctx = None

from ._args import args

if TYPE_CHECKING:
    from typing import Any, Generator

    from kaleido import FigureDict
    from kaleido._utils import fig_tools

_logger = logistro.getLogger(__name__)


def get_mocks_in_paths(path: str | Path) -> list[Path]:
    # Work with Paths and directories
    path = Path(path) if isinstance(path, str) else path

    if path.is_dir():
        _logger.info(f"Input is path {path}")
        return list(path.glob("*.json")) + list(path.glob("*.pkl.zst"))
    elif path.is_file():
        _logger.info(f"Input is file {path}")
        return [path]
    else:
        raise TypeError("--input must be file or directory")


class Param(TypedDict):
    name: str
    opts: dict[str, int | float]


# maybe don't have this do params and figures
def load_figures_from_paths(paths: list[Path]) -> Generator[FigureDict, Any, Any]:
    # Set json
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"Path {path} is not a file.")
        _logger.info(f"Found file: {path!s}")
        if path.suffix == ".json":
            with path.open(encoding="utf-8") as file:
                figure = orjson.loads(file.read())
        elif path.suffixes[-2:] == [".pkl", ".zst"]:
            if not dctx:
                raise RuntimeError(
                    "Decompressing pickles requires `pickles` optional dep-group.",
                )
            with path.open("rb") as file:
                binary = dctx.decompress(file.read())
                figure = pickle.loads(binary)  # noqa: S301 pickle warning
        else:
            warnings.warn(
                f"Unrecognized path type, skipping: {path}",
                category=UserWarning,
                stacklevel=2,
            )
            continue
        for f, w, h, s in itertools.product(  # all combos
            args.format,
            args.width,
            args.height,
            args.scale,
        ):
            name = (
                f"{path.stem}.{f!s}"
                if not args.parameterize
                else f"{path.stem!s}-{w!s}x{h!s}@{s!s}.{f!s}"
            )
            opts: fig_tools.LayoutOpts = {
                "scale": s,
                "width": w,
                "height": h,
            }
            _logger.info(f"Yielding spec: {name!s}")
            _r: FigureDict = {
                "fig": figure,
                "path": str(Path(args.output) / name),
                "opts": opts,
            }
            yield _r
