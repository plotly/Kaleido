from pathlib import Path
import base64
import json


# constants
DEFAULT_FORMAT = "png"
DEFAULT_SCALE = 1
DEFAULT_WIDTH = 700
DEFAULT_HEIGHT = 500
TEXT_FORMATS = ("svg", "json")  # eps
SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "webp", "svg", "json")  # pdf and eps


def get_layout_info(layout_opts):
    format = (
        layout_opts.get("format", DEFAULT_FORMAT) if layout_opts else DEFAULT_FORMAT
    )
    width = layout_opts.get("width", DEFAULT_WIDTH) if layout_opts else DEFAULT_WIDTH
    height = (
        layout_opts.get("height", DEFAULT_HEIGHT) if layout_opts else DEFAULT_HEIGHT
    )
    scale = layout_opts.get("scale", DEFAULT_SCALE) if layout_opts else DEFAULT_SCALE
    return format, width, height, scale


def get_figure_dimensions(layout, width, height):
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


def get_format(format):
    # Normalize format
    original_format = format
    format = format.lower()
    if format == "jpg":
        format = "jpeg"

    if format not in SUPPORTED_FORMATS:
        supported_formats_str = repr(list(SUPPORTED_FORMATS))
        raise ValueError(
            "Invalid format '{original_format}'.\n"
            "    Supported formats: {supported_formats_str}".format(
                original_format=original_format,
                supported_formats_str=supported_formats_str,
            )
        )
    return format


def to_spec(figure, layout_opts):
    # Extract info
    format, width, height, scale = get_layout_info(layout_opts)

    # TODO: validate args
    if hasattr(figure, "to_dict"):
        figure = figure.to_dict()

    # Get figure layout
    layout = figure.get("layout", {})

    # Compute image width / height
    width, height = get_figure_dimensions(layout, width, height)

    format = get_format(format)

    js_args = dict(format=format, width=width, height=height, scale=scale)
    return dict(js_args, data=figure)


def from_response(response):
    # Check for export error, later can customize error messages for plotly Python users
    code = response.get("code", 0)
    if code != 0:
        message = response.get("message", None)
        raise ValueError(
            "Transform failed with error code {code}: {message}".format(
                code=code, message=message
            )
        )
    try:
        js_response = json.loads(response.get("result").get("result").get("value"))
        response_format = js_response.get("format")
        img = js_response.get("result")
    except Exception as e:
        raise RuntimeError(response) from e

    # Base64 decode binary types
    if response_format not in TEXT_FORMATS:
        img = base64.b64decode(img)
    else:
        img = str.encode(img)
    return img


def _write_file(img_data, output_file):
    try:
        # Write image file
        with open(output_file, "wb") as out_file:
            out_file.write(img_data)
    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        raise
