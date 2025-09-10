"""
Tools to help prepare data for plotly.js from kaleido.

It 1. validates, 2. write defaults, 3. packages object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

import logistro

from . import _utils

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from typing_extensions import TypeGuard

    Figurish = Any  # Be nice to make it more specific, dictionary or something
    FormatString = Literal["png", "jpg", "jpeg", "webp", "svg", "json", "pdf"]


# Input of to_spec (user gives us this)
class LayoutOpts(TypedDict, total=False):
    format: FormatString | None
    scale: int | float
    height: int | float
    width: int | float


# Output of to_spec (we give kaleido_scopes.js this)
# refactor note: this could easily be right before send
class Spec(TypedDict):
    format: FormatString
    width: int | float
    height: int | float
    scale: int | float
    data: Figurish


_logger = logistro.getLogger(__name__)

# constants
DEFAULT_EXT = "png"
DEFAULT_SCALE = 1
DEFAULT_WIDTH = 700
DEFAULT_HEIGHT = 500
SUPPORTED_FORMATS: tuple[FormatString, ...] = (
    "png",
    "jpg",
    "jpeg",
    "webp",
    "svg",
    "json",
    "pdf",
)


# validation function
def is_figurish(o: Any) -> TypeGuard[Figurish]:
    valid = hasattr(o, "to_dict") or (isinstance(o, dict) and "data" in o)
    if not valid:
        _logger.debug(
            f"Figure has to_dict? {hasattr(o, 'to_dict')} "
            f"is dict? {isinstance(o, dict)} "
            f"Keys: {o.keys() if hasattr(o, 'keys') else None!s}",
        )
    return valid


def _coerce_format(extension: str) -> FormatString:
    # wrap this condition as a typeguard for typechecker's sake
    def is_fmt(s: str) -> TypeGuard[FormatString]:
        return s in SUPPORTED_FORMATS

    formatted_extension = extension.lower()
    if formatted_extension == "jpg":
        return "jpeg"
    elif not is_fmt(formatted_extension):
        raise ValueError(
            f"Invalid format '{formatted_extension}'.\n"
            f"Supported formats: {SUPPORTED_FORMATS!s}",
        )
    else:
        return formatted_extension


def coerce_for_js(
    fig: Figurish,
    path: Path | str | None,
    opts: LayoutOpts | None,
) -> Spec:
    if not is_figurish(fig):  # VALIDATE FIG
        raise TypeError("Figure supplied doesn't seem to be a valid plotly figure.")
    if hasattr(fig, "to_dict"):  # COERCE FIG
        fig = fig.to_dict()

    path = _utils.get_path(path) if path else None

    opts = opts or {}

    if _rest := opts - LayoutOpts.__annotations__.keys():
        raise AttributeError(f"Unknown key(s) in layout options: {_rest}")

    # Extract info
    file_format = _coerce_format(
        opts.get("format")
        or (path.suffix.lstrip(".") if path and path.suffix else DEFAULT_EXT),
    )

    layout = fig.get("layout", {})

    width = (
        opts.get("width")
        or layout.get("width")
        or layout.get("template", {}).get("layout", {}).get("width")
        or DEFAULT_WIDTH
    )

    height = (
        opts.get("height")
        or layout.get("height")
        or layout.get("template", {}).get("layout", {}).get("height")
        or DEFAULT_HEIGHT
    )

    scale = opts.get("scale", DEFAULT_SCALE)

    # PACKAGING
    spec: Spec = {
        "format": file_format,
        "width": width,
        "height": height,
        "scale": scale,
        "data": fig,
    }

    return spec
