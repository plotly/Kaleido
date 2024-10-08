# don't use scopes!
from pathlib import Path
import asyncio
import base64
import json

from devtools import Browser

script_path = Path(__file__).resolve().parent / "vendor" / "index.html"

_all_formats_ = ("png", "jpg", "jpeg", "webp", "svg", "pdf", "eps", "json")
_text_formats_ = ("svg", "json", "eps")

_scope_flags_ = ("plotlyjs", "mathjax", "topojson", "mapbox_access_token")

def to_image_block(spec):
    loop = None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        pass
    if loop:
        # TODO: create thread and post the new loop there and run the thing and return it in a message queue :-(
        ...
    else:
        return asyncio.run(to_image(spec))

async def to_image(spec):
    async with Browser(headless=False) as browser:
        tab = await browser.create_tab(script_path.as_uri())
        await tab.send_command("Page.enable")
        await tab.send_command("Runtime.enable")

        event_done = asyncio.get_running_loop().create_future()
        async def execution_started_cb(response):
            event_done.set_result(response)
        tab.subscribe("Runtime.executionContextCreated", execution_started_cb, repeating=False)
        await tab.send_command("Page.reload")
        await event_done
        execution_context_id = event_done.result()["params"]["context"]["id"]
        # this could just as easily be part of the original script
        # some changes could be made their to download more easily TODO
        # read original python, read original javascript

        event_done = asyncio.get_running_loop().create_future()
        async def load_done_cb(response):
            event_done.set_result(response)
        tab.subscribe("Page.loadEventFired", load_done_cb, repeating=False)
        await event_done

        kaleido_jsfn = r"function(spec, ...args) { console.log(typeof spec); console.log(spec); return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify); }"

        params = dict(
                functionDeclaration=kaleido_jsfn,
                arguments=[dict(value=spec)],
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

        img = json.loads(response.get("result").get("result").get("value")).get("result")

        # Base64 decode binary types
        if format not in _text_formats_:
            img = base64.b64decode(img)
        return img
