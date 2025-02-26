import re
from pathlib import Path

import logistro

_logger = logistro.getLogger(__name__)

# constants
DEFAULT_EXT = "png"
DEFAULT_SCALE = 1
DEFAULT_WIDTH = 700
DEFAULT_HEIGHT = 500
SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "webp", "svg", "json", "pdf")  # pdf and eps


def _is_figurish(o):
    return hasattr(o, "to_dict") or (isinstance(o, dict) and "data" in o)


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
    # Normalize format
    original_format = extension
    extension = extension.lower()
    if extension == "jpg":
        extension = "jpeg"

    if extension not in SUPPORTED_FORMATS:
        supported_formats_str = repr(list(SUPPORTED_FORMATS))
        raise ValueError(
            f"Invalid format '{original_format}'.\n"
            f"    Supported formats: {supported_formats_str}",
        )
    return extension


def to_spec(figure, layout_opts):
    # Get figure layout
    layout = figure.get("layout", {})

    # Extract info
    extension = _get_format(layout_opts.get("format", DEFAULT_EXT))
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


def _next_filename(path, prefix, ext):
    default = 1 if (path / f"{prefix}.{ext}").exists() else 0
    re_number = re.compile(r"^" + prefix + r"-(\d+)\." + ext + r"$")
    numbers = [
        int(match.group(1))
        for name in path.glob(f"{prefix}-*.{ext}")
        if (match := re_number.match(Path(name).name))
    ]
    n = max(numbers, default=default) + 1
    return f"{prefix}.{ext}" if n == 1 else f"{prefix}-{n}.{ext}"


def build_fig_spec(fig, path, opts):
    if not opts:
        opts = {}

    if hasattr(fig, "to_dict"):
        fig = fig.to_dict()

    if isinstance(path, str):
        path = Path(path)

    if path and path.suffix and not opts.get("format"):
        opts["format"] = path.suffix.lstrip(".")

    spec = to_spec(fig, opts)

    ext = spec["format"]
    full_path = None
    if not path:
        directory = Path()
    elif path and (not path.suffix or path.is_dir()):
        if not path.is_dir():
            raise ValueError(f"Directories will not be created for you: {path}")
        directory = path
    else:
        full_path = path
        if not full_path.parent.is_dir():
            raise RuntimeError(
                f"Cannot reach path {path}. Are all directories created?",
            )
    if not full_path:
        _logger.debug("Looking for title")
        prefix = (
            fig.get("layout", {}).get("title", {}).get("text", "fig").replace(" ", "_")
        )
        _logger.debug(f"Found: {prefix}")
        name = _next_filename(directory, prefix, ext)
        full_path = directory / name

    return spec, full_path
