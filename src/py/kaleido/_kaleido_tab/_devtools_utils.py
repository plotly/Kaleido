"""Contains both DevTools protocol and kaleido_scopes.js helper fns."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING

import logistro

from ._errors import JavascriptError, KaleidoError, _get_error, _raise_error

if TYPE_CHECKING:
    from typing import Any

    import choreographer

_logger = logistro.getLogger(__name__)


def get_js_id(result) -> int:
    """Grab javascript engine ID from a chrome executionContextStarted event."""
    if _id := result.get("params", {}).get("context", {}).get("id", None):
        return _id
    raise RuntimeError(
        "Refresh sequence didn't work for reload_tab_with_javascript."
        "Result {javascript_ready.result()}.",
    )


async def console_print(tab: choreographer.Tab, js_id: int, message: str) -> None:
    """
    Print something to the javascript console.

    Note: tab and js_id need to specified separately

    Args:
        tab: the choreographer tab to print on
        js_id: the javascript engine id to print on
        message: The thing to print.

    """
    fn = r"function()" r"{" f"console.log('{message}')" r"}"
    params = {
        "functionDeclaration": fn,
        "returnByValue": False,
        "userGesture": True,
        "awaitPromise": True,
        "executionContextId": js_id,
    }

    # send request to run script in chromium
    _logger.debug("Calling js function")
    result = await tab.send_command("Runtime.callFunctionOn", params=params)
    _logger.debug(f"Sent javascript got result: {result}")
    _raise_error(result)


async def exec_js_fn(
    tab: choreographer.Tab,
    js_id: int,
    fn: str,
    *args: Any,
):
    args_structured = [{"value": arg} for arg in args]
    params = {
        "functionDeclaration": fn,
        "arguments": args_structured,
        "returnByValue": False,
        "userGesture": True,
        "awaitPromise": True,
        "executionContextId": js_id,
    }
    return await tab.send_command("Runtime.callFunctionOn", params=params)


_TEXT_FORMATS = ("svg", "json")  # eps


async def get_bytes(self, response) -> tuple[None, bytes, None | Exception]:
    # TODO(AJP) provoke a js error and return js error

    # check_js could be another function, the next two sections should be
    # factored out
    js_response = json.loads(
        response.get(
            "result",
            {},
        )
        .get(
            "result",
            {},
        )
        .get(
            "value",
        ),
    )

    if js_response["code"] != 0:
        return None, KaleidoError(js_response["code"], js_response["message"])

    # this shouldn't be in here
    if (response_format := js_response.get("format")) == "pdf":
        pdf_params = {
            "printBackground": True,
            "marginTop": 0.1,
            "marginBottom": 0.1,
            "marginLeft": 0.1,
            "marginRight": 0.1,
            "preferCSSPageSize": True,
            "pageRanges": "1",
        }
        pdf_response = await self.tab.send_command(
            "Page.printToPDF",
            params=pdf_params,
        )
        e = _get_error(pdf_response)
        if e:
            return e
        img_raw = pdf_response.get("result").get("data")
    else:
        img_raw = js_response.get("result")

    # Base64 decode binary types
    if response_format not in _TEXT_FORMATS:
        return base64.b64decode(img_raw), None
    else:
        return str.encode(img_raw), None
