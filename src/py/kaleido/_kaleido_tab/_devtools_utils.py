"""Contains both DevTools protocol and kaleido_scopes.js helper fns."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import logistro

from ._errors import KaleidoError, _raise_error

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


def check_kaleido_js_response(
    response,
) -> dict:
    _raise_error(response)
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
    if not js_response:
        raise RuntimeError(
            f"Javascript response not understood: {response}",
        )
    # NOTE: Why above "JavascriptError"
    # This is an error in extracting a response when we expected javascript.
    # If its an actual javascript error, the response will be coherent, and
    # _raise_error above will find it.

    if js_response["code"] != 0:
        raise KaleidoError(js_response["code"], js_response["message"])

    return js_response


async def print_pdf(
    tab: choreographer.Tab,
) -> str:
    pdf_params = {
        "printBackground": True,
        "marginTop": 0.1,
        "marginBottom": 0.1,
        "marginLeft": 0.1,
        "marginRight": 0.1,
        "preferCSSPageSize": True,
        "pageRanges": "1",
    }
    pdf_response = await tab.send_command(
        "Page.printToPDF",
        params=pdf_params,
    )
    _raise_error(pdf_response)
    return pdf_response.get("result", {}).get("data")  # Check for None?
