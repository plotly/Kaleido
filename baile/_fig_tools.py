# constants
DEFAULT_EXT = "png"
DEFAULT_SCALE = 1
DEFAULT_WIDTH = 700
DEFAULT_HEIGHT = 500
SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "webp", "svg", "json")  # pdf and eps


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
                f"    Supported formats: {supported_formats_str}"
                )
    return extension


def to_spec(figure, layout_opts):

    # Get figure layout
    layout = figure.get("layout", {})

    # Extract info
    extension = _get_format(
            layout_opts.get("format", DEFAULT_EXT)
            )
    width, height = _get_figure_dimensions(
            layout,
            layout_opts.get("width"),
            layout_opts.get("height")
            )
    scale = layout_opts.get("scale", DEFAULT_SCALE)


    return {
            "format":extension,
            "width":width,
            "height":height,
            "scale":scale,
            "data": figure
            }
