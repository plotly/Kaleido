# don't use scopes!
from pathlib import Path
import asyncio
import base64
import json

from choreographer import Browser


script_path = Path(__file__).resolve().parent / "vendor" / "index.html"

# pdf and eps temporarily disabled
_all_formats_ = ("png", "jpg", "jpeg", "webp", "svg", "json", "pdf") # eps missing (emf has code but no listed support)
_text_formats_ = ("svg", "json",) # eps is a text format? :-O

_scope_flags_ = ("plotlyjs", "mathjax", "topojson", "mapbox_access_token")

def to_image_block(spec, f=None, topojson=None, mapbox_token=None):
    try:
        _ = asyncio.get_running_loop()
        from threading import Thread
        image = None
        def get_image():
            nonlocal image
            image = asyncio.run(to_image(spec, f, topojson, mapbox_token))
        t = Thread(target=get_image)
        t.start()
        t.join()
        return image
    except RuntimeError:
        pass
    return asyncio.run(to_image(spec, f, topojson, mapbox_token))

async def to_image(spec, f=None, topojson=None, mapbox_token=None):
    async with Browser(headless=True) as browser:
        if not f:
            f = script_path.absolute()
        tab = await browser.create_tab(f.as_uri())
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
        if response_format == "pdf":
            pdf_params = dict(printBackground=True,
                          marginTop=0,
                          marginBottom=0,
                          marginLeft=0,
                          marginRight=0,
                          preferCSSPageSize=True,)
            pdf_response = await tab.send_command("Page.printToPDF", params=pdf_params)
            img = pdf_response.get("result").get("data")


        # Base64 decode binary types
        if response_format not in _text_formats_:
            img = base64.b64decode(img)
        else:
            img = str.encode(img)
        return img
