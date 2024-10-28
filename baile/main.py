from pathlib import Path
import os
import json
import uuid
import warnings
import asyncio

from .prepare import to_spec, from_response, write_file, DEFAULT_FORMAT
from .browser import Browser


def _verify_figures(path_figs):
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


def _verify_path_and_name(figure):
    file_path = None
    # Set json
    if os.path.isfile(figure):
        file_path = figure
        with open(figure, "r") as file:
            figure = json.load(file)
    # Set name
    name = os.path.splitext(os.path.basename(file_path))[0]
    return figure, name


async def print_todo(obj):
    print(obj["method"])

async def _run_in_chromium(tab, spec, topojson, mapbox_token):
    print(
        f"The futures in sessions {list(tab.sessions.values())[0].subscriptions_futures}"
    )

    tab.subscribe("*", print_todo)

    # subscribe events one time
    event_runtime = tab.subscribe_once("Runtime.executionContextCreated")
    #print("subscribe Runtime.executionContextCreated")
    event_page_fired = tab.subscribe_once("Page.loadEventFired")
    #print("subscribe Page.loadEventFired")

    # send request to enable target to generate events and run scripts
    await tab.send_command("Page.enable")
    print("Succes await tab.send_command('Page.enable')")
    await tab.send_command("Runtime.enable")
    print("Succes await tab.send_command('Runtime.enable')")

    # await event futures
    await event_runtime
    print(
        f"Succes await event_runtime, the subscriptions now are {list(tab.sessions.values())[0].subscriptions_futures}"
    )
    await event_page_fired
    print(
        f"Succes await event_page_fired, the subscriptions now are {list(tab.sessions.values())[0].subscriptions_futures}"
    )

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
    result = await tab.send_command("Runtime.callFunctionOn", params=params)
    print("Succes await tab.send_command('Runtime.callFunctionOn', params=params)")

    # Disable to avoid chromium fail / Error in Kaleido
    await tab.send_command("Runtime.disable")
    print("Succes await tab.send_command('Runtime.disable')")
    await tab.reload()
    print("Succes await tab.reload()")
    return result


async def _from_json_to_img(
    tab, figure, queue, layout_opts, topojson, mapbox_token, path, name
):
    # spec creation
    spec = to_spec(figure, layout_opts)

    # Comunicate and run script for image in chromium
    response = await _run_in_chromium(tab, spec, topojson, mapbox_token)

    # Get image
    img_data = from_response(response)

    # Set path of tyhe image file
    format_path = (
        layout_opts.get("format", DEFAULT_FORMAT) if layout_opts else DEFAULT_FORMAT
    )
    output_file = f"{path}/{name}.{format_path}"

    # New thread, this avoid the blocking of the event loop
    await asyncio.to_thread(write_file, img_data, output_file)

    # Put the tab in the queue
    await queue.put(tab)


async def to_image(
    path_figs, path, num_tabs=1, layout_opts=None, topojson=None, mapbox_token=None
):
    # Warning if path=None
    if not path:
        warnings.warn(
            "Image instance will not be saved as a file. Provide a path to save it.",
            UserWarning,
        )

    # Generate list of jsons
    figures = _verify_figures(path_figs)

    # Create queue
    queue = asyncio.Queue(maxsize=num_tabs + 1)
    #print(queue)

    # Browser connection
    browser = await Browser(headless=True)
    for _ in range(num_tabs):
        tab = await browser.create_tab()
        await queue.put(tab)
    #print(f"Asi estan todos los queue {queue}")

    for figure in figures:
        # Check figure and name
        figure, name = _verify_path_and_name(
            figure
        )  # This verify or can set figure and name

        tab = await queue.get()
        #print(f"Este es el tab que se obtiene {tab}")
        #print(f"Asi estan todos los queue luego del get {queue}")

        # Process the info to generate the image
        await _from_json_to_img(
            tab, figure, queue, layout_opts, topojson, mapbox_token, path, name
        )
        #print(f"Asi estan todos los queue luego del put {queue}")

    # Close Browser
    await browser.close()
