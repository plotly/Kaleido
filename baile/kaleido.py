"""the kaleido module kaleido.py provides the main classes for the kaleido package."""
from __future__ import annotations

import asyncio
import base64
import json
import warnings
from pathlib import Path
from pprint import pformat

import choreographer as choreo
import logistro
from choreographer.errors import DevtoolsProtocolError

# Path of the page to use
PAGE_PATH = (Path(__file__).resolve().parent / "vendor" / "index.html").as_uri()
TEXT_FORMATS = ("svg", "json")  # eps

_logger = logistro.getLogger(__name__)
_logger.setLevel(9)

class JavascriptError(RuntimeError): # TODO(A): process better # noqa: TD003, FIX002
    """Used to report errors from javascript."""

def _make_printer(name):
    """Create event printer for generic events. Helper function."""
    async def print_all(response):
        _logger.debug2(f"{name}:{pformat(response)}")
    return print_all

def _make_console_printer(name):
    """Create printer specifically for console events. Helper function."""
    async def console_printer(event):
        _logger.info(f"{name}:{event}") # TODO(A): process better # noqa: TD003, FIX002
    return console_printer

def _check_error(result): # Utility
    """Check browser response for errors. Helper function."""
    if "error" in result:
        raise DevtoolsProtocolError(result)
    if result.get("result", {}).get("result", {}).get("subtype", None) == "error":
        raise JavascriptError(str(result.get("result")))

# Add note about composition/inheritance
class KaleidoTab:
    """
    A Kaleido tab is a wrapped choreographer tab providing the functions we need.

    The choreographer tab can be access through the `self.tab` attribute.
    """

    def __init__(self, tab):
        """
        Create a new KaleidoTab.

        Args:
            tab: the choreographer tab to wrap.

        """
        self.tab = tab

    async def navigate(self, url: str | Path = PAGE_PATH):
        """
        Navigate to the kaleidofier script. This is effective the real initialization.

        Args:
            url: Override the location of the kaleidofier script if necessary.

        """
        tab = self.tab
        javascript_ready = tab.subscribe_once("Runtime.executionContextCreated")
        while javascript_ready.done():
            _logger.debug2("Clearing an old Runtime.executionContextCreated")
            javascript_ready = tab.subscribe_once("Runtime.executionContextCreated")

        _logger.debug2(f"Calling Page.navigate on {tab}")
        _check_error(
                await tab.send_command(
                    "Page.navigate",
                    params = {
                        "url" : url
                        }
                    )
                )
        # Must enable after navigating.
        _logger.debug2(f"Calling Page.enable on {tab}")
        _check_error(await tab.send_command("Page.enable"))
        _logger.debug2(f"Calling Runtime.enable on {tab}")
        _check_error(await tab.send_command("Runtime.enable"))

        await javascript_ready
        try:
           self._current_js_id = javascript_ready.result()["params"]["context"]["id"]
        except BaseException as e:
            raise RuntimeError(
                    "Refresh sequence didn't work for reload_tab_with_javascript."
                    "Result {javascript_ready.result()}."
                    ) from e

    async def reload(self):
        """Reload the tab, and set the javascript runtime id."""
        tab = self.tab
        _logger.debug(f"Reloading tab {tab} with javascript.")
        javascript_ready = tab.subscribe_once("Runtime.executionContextCreated")
        while javascript_ready.done():
            _logger.debug2("Clearing an old Runtime.executionContextCreated")
            javascript_ready = tab.subscribe_once("Runtime.executionContextCreated")
        is_loaded = tab.subscribe_once("Page.loadEventFired")
        while is_loaded.done():
            _logger.debug2("Clearing an old Page.loadEventFired")
            is_loaded = tab.subscribe_once("Page.loadEventFired")
        _logger.debug2(f"Calling Page.reload on {tab}")
        _check_error(await tab.send_command("Page.reload"))
        await is_loaded
        await javascript_ready
        try:
            self._current_js_id = javascript_ready.result()["params"]["context"]["id"]
        except BaseException as e:
            raise RuntimeError(
                    "Refresh sequence didn't work for reload_tab_with_javascript."
                    "Result {javascript_ready.result()}."
                    ) from e

    async def console_print(self, message: str) -> None:
        """
        Print something to the javascript console.

        Args:
            message: The thing to print.

        """
        jsfn = (
                r"function()"
                r"{"
                f"console.log('{message}')"
                r"}"
                )
        params = {
            "functionDeclaration":jsfn,
            "returnByValue":False,
            "userGesture":True,
            "awaitPromise":True,
            "executionContextId":self._current_js_id,
            }

        # send request to run script in chromium
        _logger.debug("Calling js function")
        result = await self.tab.send_command("Runtime.callFunctionOn", params=params)
        _logger.debug(f"Sent javascript got result: {result}")
        _check_error(result)

    async def _load_spec(self, spec, *, topojson, mapbox_token):
        """
        Call the plotly renderer via javascript.

        Args:
            spec: the processed plotly figure
            topojson: a link ??? TODO
            mapbox_token: a mapbox api token for plotly to use

        """
        tab = self.tab
        execution_context_id = self._current_js_id

        # js script
        kaleido_jsfn = (
                r"function(spec, ...args)"
                r"{"
                r"return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify);"
                r"}"
                )

        # params
        arguments = [{"value":spec}]
        if topojson:
            arguments.append({"value":topojson})
        if mapbox_token:
            arguments.append({"value":mapbox_token})
        params = {
            "functionDeclaration":kaleido_jsfn,
            "arguments":arguments,
            "returnByValue":False,
            "userGesture":True,
            "awaitPromise":True,
            "executionContextId":execution_context_id,
            }

        # send request to run script in chromium
        result = await tab.send_command("Runtime.callFunctionOn", params=params)
        _check_error(result)

        return self._img_from_response(result)

    def _img_from_response(self, response):
        js_response = json.loads(response.get("result").get("result").get("value"))
        response_format = js_response.get("format")
        img = js_response.get("result")

        # Base64 decode binary types
        if response_format not in TEXT_FORMATS:
            img = base64.b64decode(img)
        else:
            img = str.encode(img)
        return img


class Kaleido(choreo.Browser):
    """Kaleido manages a set of image processors."""

    tabs_ready: asyncio.Queue[KaleidoTab]
    _tabs_in_use: set[KaleidoTab]

    def __init__(self, *args, **kwargs):
        """Initialize Kaleido, a choero.Browser wrapper adding kaleido functionality."""
        self.n = kwargs.pop("n", 1)
        self.height = kwargs.pop("height", None)
        self.width = kwargs.pop("width", None)
        if not kwargs.get("headless", True) and (self.height or self.width):
            warnings.warn(
                    "Height and Width can only be used if headless=True, "
                    "ignoring both sizes.",
                    stacklevel=1
                    )
            self.height = None
            self.width = None
        self.tabs_ready = asyncio.Queue(maxsize=0)
        self._tabs_in_use = set()
        super().__init__(*args, **kwargs)

    async def _conform_tabs(self, tabs = None, url: str | Path = PAGE_PATH) -> None:
        if not tabs:
            tabs = list(self.tabs.values())
        _logger.info(f"Conforming {len(self.tabs)} to {url}")

        for i, tab in enumerate(tabs):
            n = f"tab-{i!s}"
            _logger.debug2(f"Subscribing * to tab: {tab}.")
            tab.subscribe("*", _make_printer(n + " event"))
            _logger.debug2("Subscribing to all console prints for tab {tab}.")
            tab.subscribe("Runtime.consoleAPICalled", _make_console_printer(n))

        _logger.debug("Navigating all tabs")

        kaleido_tabs = [ KaleidoTab(tab) for tab in tabs ]

        # A little hard to read because we don't have TaskGroup in this version
        tab_tasks = [
                     (tab, asyncio.create_task(tab.navigate(url)))
                     for tab in kaleido_tabs
                     ]
        for tab, task in tab_tasks:
            await task
            await self.tabs_ready.put(tab)
        _logger.debug("Tabs fully navigated/enabled/ready")

    async def populate_targets(self) -> None:
        """Override the browser populate_targets to ensure the correct page."""
        await super().populate_targets()
        await self._conform_tabs()
        needed_tabs = self.n - len(self.tabs)
        if not needed_tabs:
            return
        tasks = [
                 asyncio.create_task(self.create_kaleido_tab())
                 for _ in range(needed_tabs)
                 ]
        for task in tasks:
            await task


    async def create_kaleido_tab(
            self,
            url : str = PAGE_PATH,
            ) -> None:
        """
        Create a tab with the kaleido script.

        Args:
            url: override the url of the kaleidofier script if desired.

        Returns:
            The kaleido-tab created.

        """
        tab = await super().create_tab(url=url, width=self.width, height=self.height)
        await self._conform_tabs([tab])


    async def get_kaleido_tab(self) -> KaleidoTab:
        """
        Retreive an available tab from queue.

        Returns:
            A kaleido-tab from the queue.

        """
        tab = await self.tabs_ready.get()
        while tab in self._tabs_in_use:
            tab = await self.tabs_ready.get()
        self._tabs_in_use.add(tab)
        _logger.debug(f"Got {tab}")
        return tab


    async def return_kaleido_tab(self, tab):
        """
        Refresh tab and put it back into the available queue.

        Args:
            tab: the kaleido tab to return.

        """
        await tab.reload()
        self._tabs_in_use.remove(tab)
        await self.tabs_ready.put(tab)
