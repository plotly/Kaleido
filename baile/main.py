from pathlib import Path
import os
import sys
import json
import asyncio
import async_timeout as atimeout

from .fig_properties import to_spec, from_response, _write_file, DEFAULT_FORMAT
from .browser import Browser
import choreographer as choreo
import logistro as logging


def _get_json_path(path_figs):
    # Work with Paths and directories
    if isinstance(path_figs, str):
        figures = Path(path_figs)
    else:
        figures = path_figs

    # Return list
    if os.path.isdir(path_figs):
        return [str(figures / a) for a in os.listdir(figures) if a.endswith(".json")]
    else:
        # If is just one dir or path
        return [path_figs]


def _load_figure(figure):
    file_path = None
    # Set json
    if os.path.isfile(figure):
        file_path = figure
        with open(figure, "r") as file:
            figure = json.load(file)
    # Set name
    name = os.path.splitext(os.path.basename(file_path))[0]
    return figure, name


async def print_from_event(obj):
    logging.info(f"Event in Tab: {obj['method']}")
    if obj["method"] == "Runtime.consoleAPICalled":
        logging.info(obj)


async def _generate_image(tab, spec, topojson, mapbox_token, debug):
    logging.info(
        f"The futures in sessions {list(tab.sessions.values())[0].subscriptions_futures}"
    )

    if debug and "*" not in list(tab.sessions.values())[0].subscriptions:
        tab.subscribe("*", print_from_event)

    # subscribe events one time
    event_runtime = tab.subscribe_once("Runtime.executionContextCreated")
    logging.debug1("subscribe Runtime.executionContextCreated")

    event_page_fired = tab.subscribe_once("Page.loadEventFired")
    logging.debug1("subscribe Page.loadEventFired")

    # send request to enable target to generate events and run scripts
    response = await tab.send_command("Page.enable")
    if "error" in response:
        raise RuntimeError(
            "Could not enable the Page"
        ) from choreo.DevtoolsProtocolError(response)
    logging.debug2("Success await tab.send_command('Page.enable')")

    await tab.reload()
    logging.debug2("Success await tab.reload()")

    await event_page_fired
    logging.debug2(
        f"Succes await event_page_fired, the subscriptions now are {list(tab.sessions.values())[0].subscriptions_futures}"
    )

    response = await tab.send_command("Runtime.enable")
    if "error" in response:
        raise RuntimeError(
            "Could not enable the Runtime"
        ) from choreo.DevtoolsProtocolError(response)
    logging.debug1("Success await tab.send_command('Runtime.enable')")

    # await event futures
    await event_runtime
    logging.debug1(
        f"Success await event_runtime, the subscriptions now are {list(tab.sessions.values())[0].subscriptions_futures}"
    )

    # use event result
    execution_context_id = event_runtime.result()["params"]["context"]["id"]

    # js script
    kaleido_jsfn = r"function(spec, ...args) { return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify); }"

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
    result = await tab.send_command("Runtime.callFunctionOn", params=params)
    if "error" in result:
        raise RuntimeError(
            "Could not run callFunctionOn in Runtime"
        ) from choreo.DevtoolsProtocolError(result)
    logging.debug2(
        "Succes await tab.send_command('Runtime.callFunctionOn', params=params)"
    )

    return result


async def _run_kaleido_in_tab(
    tab, figure, queue, layout_opts, topojson, mapbox_token, path, name, debug
):
    # spec creation
    spec = to_spec(figure, layout_opts)

    logging.debug1("Calling chromium".center(50, "*"))
    # Comunicate and run script for image in chromium
    response = await _generate_image(tab, spec, topojson, mapbox_token, debug)

    # Get image
    img_data = from_response(response)

    # Set path of tyhe image file
    format_path = (
        layout_opts.get("format", DEFAULT_FORMAT) if layout_opts else DEFAULT_FORMAT
    )
    output_file = f"{path}/{name}.{format_path}"
    logging.debug1("Writing file".center(50, "*"))
    # New thread, this avoid the blocking of the event loop
    await asyncio.to_thread(_write_file, img_data, output_file)
    logging.debug1("Returning tab".center(50, "*"))
    # Put the tab in the queue
    await queue.put(tab)


async def create_image(
    path_figs,
    path,
    num_tabs=1,
    layout_opts=None,
    topojson=None,
    mapbox_token=None,
    debug=None,
    headless=True,
):

    if debug:
        logging.logger.setLevel(logging.DEBUG2)

    # Warning if path=None
    if not path:
        logging.warning(
            "Image instance will not be saved as a file. Provide a path to save it."
        )

    # Generate list of jsons
    figures = _get_json_path(path_figs)

    # Create queue
    queue = asyncio.Queue(maxsize=num_tabs + 1)

    # Browser connection
    async with (
        Browser(headless=headless, debug=debug, debug_browser=debug) as browser,
    ):

        async def print_all(r):
            logging.info(f"All subscription: {r}")

        if debug:
            browser.subscribe("*", print_all)
        for _ in range(num_tabs):
            tab = await browser.create_tab()
            await queue.put(tab)

        for figure in figures:
            # Check figure and name
            figure, name = _load_figure(
                figure
            )  # This verify or can set figure and name
            if name.startswith("mapbox"):
                continue
            logging.debug1("Got figure, getting tab".center(50, "*"))
            tab = await queue.get()
            logging.debug1(
                f"Awaiting wrapper for img {name} {path} on tab {tab}".center(100, "*")
            )
            async with atimeout.timeout(60 * 5) as cm:
                await _run_kaleido_in_tab(
                    tab,
                    figure,
                    queue,
                    layout_opts,
                    topojson,
                    mapbox_token,
                    path,
                    name,
                    debug,
                )
            logging.info(f"Timeout result: {cm.expired}")
