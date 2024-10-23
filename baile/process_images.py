from pathlib import Path
import os
import base64
import json
import uuid

from choreographer import Browser

# constants
SCRIPT_PATH = Path(__file__).resolve().parent / "vendor" / "index.html"
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


def verify_format(format):
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

    format = verify_format(format)

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


async def write_file(img_data, output_file):
    # Write image file
    with open(output_file, "wb") as out_file:
        out_file.write(img_data)


async def to_image(
    figure, layout_opts=None, topojson=None, mapbox_token=None, path=None, name=None
):
    file_path = None
    # Set json
    if os.path.isfile(figure):
        file_path = figure
        with open(figure, "r") as file:
            figure = json.load(file)

    # Set name
    if file_path and not name:
        name = os.path.splitext(os.path.basename(file_path))[0]
    elif not name:
        name = uuid.uuid4()

    # spec creation
    spec = to_spec(figure, layout_opts)

    # Browser connection
    async with Browser(headless=True) as browser:
        tab = await browser.create_tab(SCRIPT_PATH.as_uri())

        # subscribe events one time
        event_runtime = tab.subscribe_once("Runtime.executionContextCreated")
        event_page_fired = tab.subscribe_once("Page.loadEventFired")

        # send request to enable target to generate events and run scripts
        await tab.send_command("Page.enable")
        await tab.send_command("Runtime.enable")

        # await event futures
        await event_runtime
        await event_page_fired

        # use event result
        execution_context_id = event_runtime.result()["params"]["context"]["id"]

        # js script
        kaleido_jsfn = r"function(spec, ...args) { console.log(typeof spec); console.log(spec); return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify); }"

        # params
        arguments = [dict(value=spec)]
        if topojson:
            arguments.append(dict(value=topojson))
        if mapbox_token:
            arguments.append(dict(value=mapbox_token))
        params = dict(
            functionDeclaration=kaleido_jsfn,
            arguments=arguments,
            returnByValue=False,
            userGesture=True,
            awaitPromise=True,
            executionContextId=execution_context_id,
        )

        # send request to run script in chromium
        response = await tab.send_command("Runtime.callFunctionOn", params=params)

        if path:
            # Get image
            img_data = from_response(response)

            # Set path of tyhe image file
            format_path = (
                layout_opts.get("format", DEFAULT_FORMAT)
                if layout_opts
                else DEFAULT_FORMAT
            )
            output_file = f"{path}/{name}.{format_path}"

            await write_file(img_data, output_file)
            return img_data
        return from_response(response)
