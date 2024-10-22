from pathlib import Path
import asyncio
import base64
import json

from choreographer import Browser

script_path = Path(__file__).resolve().parent / "index.html"

# pdf and eps temporarily disabled

_text_formats_ = (
    "svg",
    "json",
)  # eps


def to_spec(figure, format=None, width=None, height=None, scale=None):
    default_format = "png"
    default_scale = 1
    default_width = 700
    default_height = 500
    _all_formats = ("png", "jpg", "jpeg", "webp", "svg", "json")  # pdf and eps
    # TODO: validate args
    if hasattr(figure, "to_dict"):
        figure = figure.to_dict()

    # Apply default format and scale
    format = format if format is not None else default_format
    scale = scale if scale is not None else default_scale

    # Get figure layout
    layout = figure.get("layout", {})

    # Compute image width / height
    width = (
        width
        or layout.get("width", None)
        or layout.get("template", {}).get("layout", {}).get("width", None)
        or default_width
    )
    height = (
        height
        or layout.get("height", None)
        or layout.get("template", {}).get("layout", {}).get("height", None)
        or default_height
    )

    # Normalize format
    original_format = format
    format = format.lower()
    if format == "jpg":
        format = "jpeg"

    if format not in _all_formats:
        supported_formats_str = repr(list(_all_formats))
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
        tab = await browser.create_tab(script_path.as_uri())
        event_runtime = tab.subscribe_once("Runtime.executionContextCreated")
        event_page_fired = tab.subscribe_once("Page.loadEventFired")
        await tab.send_command("Page.enable")
        await tab.send_command("Runtime.enable")
        await event_runtime
        execution_context_id = event_runtime.result()["params"]["context"]["id"]
        # this could just as easily be part of the original script
        # some changes could be made their to download more easily TODO
        # read original python, read original javascript
        await event_page_fired

        kaleido_jsfn = r"function(spec, ...args) { console.log(typeof spec); console.log(spec); return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify); }"
        spec = to_spec(figure, format=format, width=width, height=height, scale=scale)
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
        if response_format not in _text_formats_:
            img = base64.b64decode(img)
        else:
            img = str.encode(img)
        return img
