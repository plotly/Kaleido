import os
import json
import uuid
import warnings
import asyncio

from .prepare import to_spec, from_response, write_file, DEFAULT_FORMAT
from .browser import Browser


def _verify_path_and_name(figure, name):
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
    return figure, name


async def _run_in_chromium(tab, spec, topojson, mapbox_token):
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
    return await tab.send_command("Runtime.callFunctionOn", params=params)


async def _from_json_to_img(
    tab, figure, layout_opts, topojson, mapbox_token, path, name
):
    # spec creation
    spec = to_spec(figure, layout_opts)

    # Comunicate and run script for image in chromium
    response = await _run_in_chromium(tab, spec, topojson, mapbox_token)

    if path:
        # Get image
        img_data = from_response(response)

        # Set path of tyhe image file
        format_path = (
            layout_opts.get("format", DEFAULT_FORMAT) if layout_opts else DEFAULT_FORMAT
        )
        output_file = f"{path}/{name}.{format_path}"

        # New thread, this avoid the blocking of the event loop
        await asyncio.to_thread(write_file, img_data, output_file)
        return img_data
    return from_response(response)


async def to_image(
    figure, layout_opts=None, topojson=None, mapbox_token=None, path=None, name=None
):
    # Warning if path=None
    if not path:
        warnings.warn(
            "Image instance will not be saved as a file. Provide a path to save it.",
            UserWarning,
        )

    # Browser connection
    async with Browser(headless=True) as browser:
        tab = await browser.create_tab()

        figure, name = _verify_path_and_name(figure, name)

        result = await _from_json_to_img(
            tab, figure, layout_opts, topojson, mapbox_token, path, name
        )

        return result
