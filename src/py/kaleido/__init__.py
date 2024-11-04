# don't use scopes!
from pathlib import Path
import asyncio
import base64
import json
import sys
import os

import async_timeout as atimeout

from choreographer import Browser


script_path = Path(__file__).resolve().parent / "vendor" / "index.html"

# pdf and eps temporarily disabled
_all_formats_ = ("png", "jpg", "jpeg", "webp", "svg", "json", "pdf") # eps missing (emf has code but no listed support)
_text_formats_ = ("svg", "json",) # eps is a text format? :-O

_scope_flags_ = ("plotlyjs", "mathjax", "topojson", "mapbox_access_token")

def to_image_block(spec, f=None, topojson=None, mapbox_token=None, debug=None):
    if debug is None:
        debug = "KALEIDO-DEBUG" in os.environ
    try:
        _ = asyncio.get_running_loop()
        if debug: print("Got running loop, threading", file=sys.stderr)
        from threading import Thread
        image = None
        def get_image():
            nonlocal image
            if debug: print("Calling to_image in thread", file=sys.stderr)
            image = asyncio.run(to_image(spec, f, topojson, mapbox_token, debug=debug))
        t = Thread(target=get_image)
        if debug: print("Calling thread start", file=sys.stderr)
        t.start()
        t.join()
        if debug: print("Done with thread", file=sys.stderr)
        return image
    except RuntimeError:
        if debug: print("No loop, no thread", file=sys.stderr)
        pass
    return asyncio.run(to_image(spec, f, topojson, mapbox_token, debug=debug))

async def to_image(spec, f=None, topojson=None, mapbox_token=None, debug=None, timeout=60):
    if debug is None:
        debug = "KALEIDO-DEBUG" in os.environ
    def check_error(res):
        if 'error' in res:
            raise RuntimeError(str(res))

    async with (
            Browser(headless=True, debug=debug, debug_browser=sys.stderr) as browser,
            atimeout.timeout(timeout)):
        async def print_all(r):
            print(f"All subscription: {r}", file=sys.stderr)
        if debug: browser.subscribe("*", print_all)
        if not f:
            f = script_path.absolute()
        if debug: print(f"Creating tab w/ file: {f.as_uri()}", file=sys.stderr)
        tab = await browser.create_tab(f.as_uri())

        if debug: tab.subscribe("*", print_all)
        if debug: print("Activating page", file=sys.stderr)
        res = await tab.send_command("Page.bringToFront")
        check_error(res)

        page_loaded = tab.subscribe_once("Page.loadEventFired")

        if debug: print("Enabling page", file=sys.stderr)
        res = await tab.send_command("Page.enable")
        check_error(res)

        while page_loaded.done():
            print("Clearing previous loadEventFired", file=sys.stderr)
            page_loaded = tab.subscribe_once("Page.loadEventFired")

        if debug: print("About to reload page", file=sys.stderr)
        res = await tab.send_command("Page.reload")
        check_error(res)

        await page_loaded

        javascript_enabled = tab.subscribe_once("Runtime.executionContextCreated")
        while javascript_enabled.done():
            print("Clearing previous executionContextCreated", file=sys.stderr)
            javascript_enabled = tab.subscribe_once("Runtime.executionContextCreated")

        if debug: print("Enabling runtime", file=sys.stderr)
        res = await tab.send_command("Runtime.enable")
        check_error(res)

        if debug: print("Waiting executionContextCreated", file=sys.stderr)

        await javascript_enabled
        execution_context_id = javascript_enabled.result()["params"]["context"]["id"]
        # this could just as easily be part of the original script
        # some changes could be made their to download more easily TODO
        # read original python, read original javascript


        if debug:
            debug_jsfn = r"function() { return window.KaleidoReport; }"
            params = dict(
                    functionDeclaration=debug_jsfn,
                    returnByValue=True,
                    executionContextId=execution_context_id)
            print(await tab.send_command("Runtime.callFunctionOn", params=params), file=sys.stderr)



        kaleido_jsfn = r"function(spec, ...args) { return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify); }"
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
        if debug: print("Sending command", file=sys.stderr)
        response = await tab.send_command("Runtime.callFunctionOn", params=params)
        check_error(response)
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
            if debug: print("Loading result", file=sys.stderr)
            js_response = json.loads(response.get("result").get("result").get("value"))
            if debug: print(f"Received: {js_response}", file=sys.stderr)
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
            if debug: print("Sending command to print pdf", file=sys.stderr)
            pdf_response = await tab.send_command("Page.printToPDF", params=pdf_params)
            check_error(pdf_response)
            img = pdf_response.get("result").get("data")


        # Base64 decode binary types
        if response_format not in _text_formats_:
            img = base64.b64decode(img)
        else:
            img = str.encode(img)
        return img
