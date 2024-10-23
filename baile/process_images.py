from pathlib import Path
import base64
import json

from choreographer import Browser

# constants
SCRIPT_PATH = Path(__file__).resolve().parent / "vendor" / "index.html"
DEFAULT_FORMAT = "png"
DEFAULT_SCALE = 1
DEFAULT_WIDTH = 700
DEFAULT_HEIGHT = 500
TEXT_FORMATS = ("svg", "json",)  # eps
SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "webp", "svg", "json")  # pdf and eps



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


def to_spec(figure, format=None, width=None, height=None, scale=None):
    # TODO: validate args
    if hasattr(figure, "to_dict"):
        figure = figure.to_dict()

    # Apply default format and scale
    format = format if format is not None else DEFAULT_FORMAT
    scale = scale if scale is not None else DEFAULT_SCALE

    # Get figure layout
    layout = figure.get("layout", {})

    # Compute image width / height
    width, height = get_figure_dimensions(layout, width, height)

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

    js_args = dict(format=format, width=width, height=height, scale=scale)
    return dict(js_args, data=figure)


async def to_image(
    figure,
    format=None,
    width=None,
    height=None,
    scale=None,
    topojson=None,
    mapbox_token=None,
):
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
        execution_context_id = event_runtime.result()["params"]["context"]["id"]
        await event_page_fired

        # js script
        kaleido_jsfn = r"function(spec, ...args) { console.log(typeof spec); console.log(spec); return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify); }"

        # spec creation
        spec = to_spec(figure, format=format, width=width, height=height, scale=scale)

        # params
        extra_args = []
        if topojson:
            extra_args.append(dict(value=topojson))
        if mapbox_token:
            extra_args.append(dict(value=mapbox_token))
        arguments = [dict(value=spec)]
        arguments.extend(extra_args)
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
