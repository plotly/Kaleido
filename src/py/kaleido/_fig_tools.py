from __future__ import annotations

import glob
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypedDict

import logistro

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

_logger = logistro.getLogger(__name__)

# constants
DEFAULT_EXT = "png"
DEFAULT_SCALE = 1
DEFAULT_WIDTH = 700
DEFAULT_HEIGHT = 500
SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "webp", "svg", "json", "pdf")
FormatString = Literal["png", "jpg", "jpeg", "webp", "svg", "json", "pdf"]


def _assert_format(ext: str) -> TypeGuard[FormatString]:
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"File format {ext} is not supported.")
    return True


Figurish = Any  # Be nice to make it more specific, dictionary or something


def _is_figurish(o) -> TypeGuard[Figurish]:
    valid = hasattr(o, "to_dict") or (isinstance(o, dict) and "data" in o)
    if not valid:
        _logger.debug(
            f"Figure has to_dict? {hasattr(o, 'to_dict')} "
            f"is dict? {isinstance(o, dict)} "
            f"Keys: {o.keys() if hasattr(o, 'keys') else None!s}",
        )
    return valid


def _get_figure_dimensions(layout, width, height):
    # Compute image width / height with fallbacks
    width = (
        width
        or layout.get("width")
        or layout.get("template", {}).get("layout", {}).get("width")
        or DEFAULT_WIDTH
    )
    height = (
        height
        or layout.get("height")
        or layout.get("template", {}).get("layout", {}).get("height")
        or DEFAULT_HEIGHT
    )
    return width, height


def _get_format(extension):
    original_format = extension
    extension = extension.lower()
    if extension == "jpg":
        return "jpeg"

    if extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Invalid format '{original_format}'.\n"
            f"    Supported formats: {SUPPORTED_FORMATS!s}",
        )
    return extension


# Input of to_spec
class LayoutOpts(TypedDict, total=False):
    format: FormatString | None
    scale: int | float
    height: int | float
    width: int | float


# Output of to_spec
class Spec(TypedDict):
    format: FormatString
    width: int | float
    height: int | float
    scale: int | float
    data: Figurish


def to_spec(figure, layout_opts: LayoutOpts) -> Spec:
    # Get figure layout
    layout = figure.get("layout", {})

    for k, v in layout_opts.items():
        if k == "format":
            if v is not None and not isinstance(v, (str)):
                raise TypeError(
                    f"{k} must be one of {SUPPORTED_FORMATS!s} or None, not {v}.",
                )
        elif k in ("scale", "height", "width"):
            if v is not None and not isinstance(v, (float, int)):
                raise TypeError(f"{k} must be numeric or None, not {v}.")
        else:
            raise AttributeError(f"Unknown key in layout options, {k}")

    # Extract info
    extension = _get_format(layout_opts.get("format") or DEFAULT_EXT)
    width, height = _get_figure_dimensions(
        layout,
        layout_opts.get("width"),
        layout_opts.get("height"),
    )
    scale = layout_opts.get("scale", DEFAULT_SCALE)

    return {
        "format": extension,
        "width": width,
        "height": height,
        "scale": scale,
        "data": figure,
    }


def _next_filename(path, prefix, ext) -> str:
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


def build_fig_spec(  #  noqa: C901, PLR0912
    fig: Figurish,
    path: Path | str | None,
    opts: LayoutOpts | None,
) -> tuple[Spec, Path]:
    if not opts:
        opts = {}

    if not _is_figurish(fig):
        raise TypeError("Figure supplied doesn't seem to be a valid plotly figure.")

    if hasattr(fig, "to_dict"):
        fig = fig.to_dict()

    if isinstance(path, str):
        path = Path(path)
    elif path and not isinstance(path, Path):
        raise TypeError("Path should be a string or `pathlib.Path` object (or None)")

    if path and path.suffix and not opts.get("format"):
        ext = path.suffix.lstrip(".")
        if _assert_format(ext):  # not strict necessary if but helps typeguard
            opts["format"] = ext

    spec = to_spec(fig, opts)

    ext = spec["format"]

    full_path: Path | None = None
    directory: Path
    if not path:
        directory = Path()  # use current Path
    elif path and (not path.suffix or path.is_dir()):
        if not path.is_dir():
            raise ValueError(f"Directory {path} not found. Please create it.")
        directory = path
    else:
        full_path = path
        if not full_path.parent.is_dir():
            raise RuntimeError(
                f"Cannot reach path {path.parent}. Are all directories created?",
            )
    if not full_path:
        _logger.debug("Looking for title")
        prefix = fig.get("layout", {}).get("title", {}).get("text", "fig")
        prefix = re.sub(r"[ \-]", "_", prefix)
        prefix = re.sub(r"[^a-zA-Z0-9_]", "", prefix)
        prefix = prefix or "fig"
        _logger.debug(f"Found: {prefix}")
        name = _next_filename(directory, prefix, ext)
        full_path = directory / name

    return spec, full_path
