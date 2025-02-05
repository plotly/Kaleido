"""the kaleido module kaleido.py provides the main classes for the kaleido package."""
from __future__ import annotations

import asyncio
import base64
import json
import traceback
import warnings
import sys
import time
if sys.version_info >= (3, 11):
    from asyncio import timeout
else:
    from async_timeout import timeout

from collections.abc import Iterable
from functools import partial
from pathlib import Path
from pprint import pformat

import choreographer as choreo
import logistro
from choreographer.errors import DevtoolsProtocolError

from ._fig_tools import build_fig_spec

# Path of the page to use
PAGE_PATH = (Path(__file__).resolve().parent / "vendor" / "index.html").as_uri()
TEXT_FORMATS = ("svg", "json")  # eps

_logger = logistro.getLogger(__name__)

class ErrorEntry:
    def __init__(self, name, error, javascript_log):
        self.name = name
        self.error = error
        self.javascript_log = javascript_log

    def __str__(self):
        ret = f"{self.name}:\n"
        e = self.error
        ret += " ".join(traceback.format_exception(type(e), e, e.__traceback__))
        ret += " javascript Log:\n"
        ret += "\n ".join(self.javascript_log)
        return ret

class KaleidoError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self):
        return f"Error {self.code}: {self.message}"


class JavascriptError(RuntimeError): # TODO(A): process better # noqa: TD003, FIX002
    """Used to report errors from javascript."""

def _make_printer(name):
    """Create event printer for generic events. Helper function."""
    async def print_all(response):
        _logger.debug2(f"{name}:{response}")
    return print_all

def _make_console_logger(name, log):
    """Create printer specifically for console events. Helper function."""
    async def console_printer(event):
        _logger.debug2(f"{name}:{event}") # TODO(A): parse # noqa: TD003, FIX002
        # TODO change levels depending on that first argument WARN: ERROR:
        if "params" in event and "args" in event["params"]:
            args = event["params"]["args"]
            for arg in args:
                if "type" in arg and arg["type"] == "string":
                    log.append("****string: " + arg["value"])
                elif "type" in arg and arg["type"] == "object" and "preview" in arg:
                        if arg["preview"]["description"] == "Error":
                            log.append("****Error as object:")
                            for prop in arg["preview"]["properties"]:
                                log.append(f"{prop['name']!s}: {prop['value']!s}")
                        else:
                            log.append("****Printing whole object preview")
                            log.append(str(arg["preview"]))
                else:
                    log.append("****Whole arg:")
                    log.append(str(arg))
        else:
            log.append("****Printing whole event")
            log.append(pformat(event))
    return console_printer

def _check_error_ret(result): # Utility
    """Check browser response for errors. Helper function."""
    if "error" in result:
        return DevtoolsProtocolError(result)
    if result.get("result", {}).get("result", {}).get("subtype", None) == "error":
        return JavascriptError(str(result.get("result")))
    return None

def _check_error(result):
    e = _check_error_ret(result)
    if e:
        raise e

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
        self.javascript_log = []

    def _regenerate_javascript_console(self):
        tab = self.tab
        self.javascript_log = []
        _logger.debug2("Subscribing to all console prints for tab {tab}.")
        tab.unsubscribe("Runtime.consoleAPICalled")
        tab.subscribe(
                "Runtime.consoleAPICalled",
                _make_console_logger(
                    "tab js console",
                    self.javascript_log
                    )
                )

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
        page_ready = tab.subscribe_once("Page.loadEventFired")
        while page_ready.done():
            _logger.debug2("Clearing a old Page.loadEventFired")
            page_ready = tab.subscribe_once("Page.loadEventFired")

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
        self._current_js_id = (
                javascript_ready.result()
                .get("params", {})
                .get("context", {})
                .get("id", None)
                )
        if not self._current_js_id:
            raise RuntimeError(
                    "Refresh sequence didn't work for reload_tab_with_javascript."
                    "Result {javascript_ready.result()}."
                    )
        await page_ready
        self._regenerate_javascript_console()

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
        await javascript_ready
        self._current_js_id = (
                javascript_ready.result()
                .get("params", {})
                .get("context", {})
                .get("id", None)
                )
        if not self._current_js_id:
            raise RuntimeError(
                    "Refresh sequence didn't work for reload_tab_with_javascript."
                    "Result {javascript_ready.result()}."
                    )
        await is_loaded
        self._regenerate_javascript_console()

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

    def _finish_profile(self, profile, error=None, size_mb=None):
        _logger.debug("Finishing profile")
        profile["duration"] = float(f"{time.perf_counter() - profile['start']:.6f}")
        del profile["start"]
        if self.javascript_log:
            profile["js_console"] = self.javascript_log
        if error:
            profile["error"] = error
        if size_mb:
            profile["megabytes"]  = size_mb

    async def write_fig(
            self,
            spec,
            full_path,
            *,
            topojson=None,
            mapbox_token=None,
            error_log=None,
            profiler=None,
            ):
        """
        Call the plotly renderer via javascript.

        Args:
            fig: the processed plotly figure
            path: the path to write the image too. if its a directory, we will try to
                generate a name. If the path contains an extension,
                "path/to/my_image.png", that extension will be the format used if not
                overriden in `opts`.
            opts: dictionary describing format, width, height, and scale of image
            topojson: a link ??? TODO
            mapbox_token: a mapbox api token for plotly to use

        """
        if profiler is not None:
            _logger.debug("Using profiler")
            profile = {
                    "name":full_path.name,
                    "start":time.perf_counter(),
                    }
        async with timeout(.5) as timer:
            tab = self.tab
            _logger.debug(f"In tab {tab.target_id[:4]} write_fig for {full_path.name}.")
            execution_context_id = self._current_js_id


            _logger.info(f"Processing {full_path.name}")
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
            #_logger.info(f"Activating tab for {full_path.name}.")
            #_check_error(
            #        await tab.send_command(
            #            "Target.activateTarget",
            #            params={"targetId":tab.target_id}
            #            )
            #        )
            #_logger.info(f"Activated tab for {full_path.name}.")
            _logger.info(f"Sending big command for {full_path.name}.")
            result = await tab.send_command("Runtime.callFunctionOn", params=params)
            _logger.info(f"Sent big command for {full_path.name}.")
            e = _check_error_ret(result)
            if e:
                if profiler is not None:
                    self._finish_profile(profile, e)
                    profiler[tab.target_id].append(profile)
                if error_log is not None:
                    error_log.append(ErrorEntry(full_path.name, e, self.javascript_log))
                    _logger.info(f"Failed {full_path.name}")
                    return
                else:
                    raise e
            _logger.debug2(f"Result of function call: {result}")

            img = self._img_from_response(result)
            if isinstance(img, BaseException):
                if profiler is not None:
                    self._finish_profile(profile, img)
                    profiler[tab.target_id].append(profile)
                if error_log is not None:
                    error_log.append(
                            ErrorEntry(full_path.name, img, self.javascript_log)
                            )
                    _logger.info(f"Failed {full_path.name}")
                    return
                else:
                    raise img

            def write_image(binary):
                with full_path.open("wb") as file:
                    file.write(binary)
            _logger.info(f"Starting write of {full_path.name}")
            await asyncio.to_thread(write_image, img)
            _logger.info(f"Wrote {full_path.name}")
        if profiler is not None:
            self._finish_profile(profile, e, full_path.stat().st_size/1000000)
            profiler[tab.target_id].append(profile)
        if timer.expired:
            _logger.error(f"{full_path.name} timed out.\n"
                          "\n".join(self.javascript_log))
            raise TimeoutError(f"From {full_path.name}")

    def _img_from_response(self, response):
        js_response = json.loads(response.get("result").get("result").get("value"))

        if js_response["code"] != 0:
            return KaleidoError(js_response["code"], js_response["message"])

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
    _background_render_tasks: set[asyncio.Task]
    _main_tasks: set[asyncio.Task]

    async def close(self):
        """Close the browser."""
        _logger.info("Cancelling tasks.")
        for task in self._main_tasks:
            if not task.done():
                task.cancel()
        for task in self._background_render_tasks:
            if not task.done()
                task.cancel()
        _logger.info("Exiting Kaleido/Choreo")
        return await super().close()

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        """Close the browser."""
        _logger.info("Waiting for all cleanups to finish.")
        await asyncio.gather(*self._background_render_tasks, return_exceptions=True)
        _logger.info("Exiting Kaleido")
        return await super().__aexit__(exc_type, exc_value, exc_tb)

    def __init__(self, *args, **kwargs): # noqa: D417 no args/kwargs in description
        """
        Initialize Kaleido, a `choreo.Browser` wrapper adding kaleido functionality.

        It takes all choreo.Browser args, plus some extra. Extra listed, see
        choreographer for that documentation.

        Note: Chrome will throttle background tabs and windows, so non-headless
        multi-process configurations don't work well.

        Args:
            n: the number of separate processes (windows, not seen) to use.
            timeout: limit on any ONE render.
            width: width of window (headless only)
            height: height of window (headless only)

        """
        self._background_render_tasks = set()

        self.timeout = kwargs.pop("timeout", 60)
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
        super().__init__(*args, **kwargs)

    async def _conform_tabs(self, tabs = None, url: str | Path = PAGE_PATH) -> None:
        if not tabs:
            tabs = list(self.tabs.values())
        _logger.info(f"Conforming {len(tabs)} to {url}")

        for i, tab in enumerate(tabs):
            n = f"tab-{i!s}"
            _logger.debug2(f"Subscribing * to tab: {tab}.")
            tab.subscribe("*", _make_printer(n + " event"))

        _logger.debug("Navigating all tabs")

        kaleido_tabs = [ KaleidoTab(tab) for tab in tabs ]

        # A little hard to read because we don't have TaskGroup in this version
        tasks = [
                     asyncio.create_task(tab.navigate(url))
                     for tab in kaleido_tabs
                     ]
        _logger.info("Waiting on all navigates")
        await asyncio.gather(*tasks)
        _logger.info("All navigates done, putting them all in queue.")
        for tab in kaleido_tabs:
            await self.tabs_ready.put(tab)
        _logger.debug("Tabs fully navigated/enabled/ready")

    async def populate_targets(self) -> None:
        """Override the browser populate_targets to ensure the correct page."""
        await super().populate_targets()
        await self._conform_tabs()
        needed_tabs = self.n - len(self.tabs)
        if needed_tabs < 0:
            raise RuntimeError("Did you set 0 or less tabs?")
        if not needed_tabs:
            return
        tasks = [
                 asyncio.create_task(self.create_kaleido_tab())
                 for _ in range(needed_tabs)
                 ]

        await asyncio.gather(*tasks)
        for tab in self.tabs.values():
            _logger.info(f"Tab ready: {tab.target_id}")


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
        tab = await super().create_tab(
                url=url,
                width=self.width,
                height=self.height,
                window=True
                )
        await self._conform_tabs([tab])


    async def _get_kaleido_tab(self) -> KaleidoTab:
        """
        Retreive an available tab from queue.

        Returns:
            A kaleido-tab from the queue.

        """
        _logger.info(f"Getting tab from queue (has {self.tabs_ready.qsize()})")
        tab = await self.tabs_ready.get()
        _logger.info(f"Got {tab.tab.target_id[:4]}")
        return tab


    async def _return_kaleido_tab(self, tab):
        """
        Refresh tab and put it back into the available queue.

        Args:
            tab: the kaleido tab to return.

        """
        _logger.info(f"Reloading tab {tab.tab.target_id[:4]} before return.")
        await tab.reload()
        _logger.info(f"Putting tab {tab.tab.target_id[:4]} back (queue size: {self.tabs_ready.qsize()}).")
        await self.tabs_ready.put(tab)
        _logger.debug(f"{tab.tab.target_id[:4]} put back.")

    def _clean_tab_return_task(self, main_task, task):
        _logger.info("Cleaning out background tasks.")
        self._background_render_tasks.remove(task)
        e = task.exception()
        if e:
            _logger.error("Clean tab return task found exception", exc_info=e)
            if not main_task.done():
                main_task.cancel()
            raise e

    def _check_render_task(self, name, tab, main_task, task):
        if e := task.exception():
            if isinstance(e, (asyncio.CancelledError, asyncio.TimeoutError)):
                _logger.info("Something timedout or cancelled.")
            _logger.error(f"Render Task Error In {name}- ", exc_info=e)
            if not main_task.done():
                main_task.cancel()
            raise e
        _logger.info(f"Returning {name} tab after render.")
        t = asyncio.create_task(self._return_kaleido_tab(tab))
        self._background_render_tasks.add(t)
        t.add_done_callback(partial(self._clean_tab_return_task, main_task))

    async def _render_task(self, tab, args, error_log = None, profiler = None):
        _logger.info(f"Posting a task for {args['full_path'].name}")
        await tab.write_fig(**args, error_log=error_log, profiler=profiler)
        _logger.info(f"Posted task ending for {args['full_path'].name}")

    async def write_fig( # noqa: PLR0913, C901 (too many args, complexity)
            self,
            fig,
            path = None,
            opts = None,
            *,
            topojson = None,
            mapbox_token = None,
            error_log = None,
            profiler = None,
            ):
        """
        Call the plotly renderer via javascript on first available tab.

        Args:
            fig: the plotly figure or an iterable of plotly figures
            path: the path to write the images to. if its a directory, we will try to
                generate a name. If the path contains an extension,
                "path/to/my_image.png", that extension will be the format used if not
                overriden in `opts`. If you pass a complete path (filename), for
                multiple figures, you will overwrite every previous figure.
            opts: dictionary describing format, width, height, and scale of image
            topojson: a link ??? TODO
            mapbox_token: a mapbox api token for plotly to use
            error_log: A supplied list, will be populated with `ErrorEntry`s
                       which can be converted to strings. Note, this is for
                       collections errors that have to do with plotly. They will
                       not be thrown. Lower level errors (kaleido, choreographer)
                       will still be thrown.
            profiler: A supplied empty dictionary, will be populated with information
                      about tabs, runtimes, etc.

        """
        if error_log is not None:
            _logger.info("Using error log.")
        if profiler is not None:
            _logger.info("Using profiler.")

        if hasattr(fig, "to_dict") or not isinstance(fig, Iterable):
            fig = [fig]
        else:
            _logger.debug(f"Is iterable {type(fig)}")


        main_task = asyncio.current_task()
        self._main_tasks.add(main_task)
        tasks = set()

        async def _loop(f):
            spec, full_path = build_fig_spec(f, path, opts)
            tab = await self._get_kaleido_tab()
            if profiler is not None and tab.tab.target_id not in profiler:
                profiler[tab.tab.target_id] = []
            t = asyncio.create_task(
                    self._render_task(
                        tab,
                        args = {
                            "spec" : spec,
                            "full_path" : full_path,
                            "topojson" : topojson,
                            "mapbox_token" : mapbox_token
                            },
                        ),
                    error_log = error_log,
                    profiler = profiler
                    )
            t.add_done_callback(
                    partial(
                        self._check_render_task,
                        full_path.name,
                        tab,
                        main_task
                        )
                    )
            tasks.add(t)
        try:
            if hasattr(fig, "__aiter__"): # is async iterable
                _logger.debug("Is async for")
                async for f in fig:
                    await _loop(f)
            else:
                _logger.debug("Is sync for")
                for f in fig:
                    await _loop(f)
            _logger.debug("awaiting tasks")
            await asyncio.gather(*tasks, return_exceptions=True)
        except:
            _logger.exception("Cleaning tasks after error.")
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise
        finally:
            self._main_tasks.remove(main_task)

    async def write_fig_generate_all( # noqa: C901 too complex
            self,
            generator,
            *,
            error_log = None,
            profiler = None,
            ):
        """
        Equal to `write_fig` but allows the user to generate all arguments.

        Args:
            generator: an iterable or generator which supplies a dictionary
                       of arguments to pass to tab.write_fig.
            error_log: A supplied list, will be populated with `ErrorEntry`s
                       which can be converted to strings. Note, this is for
                       collections errors that have to do with plotly. They will
                       not be thrown. Lower level errors (kaleido, choreographer)
                       will still be thrown.
            profiler: A supplied dictionary, will be populated with information
                      about tabs, runtimes, etc.

        """
        if error_log is not None:
            _logger.info("Using error log.")
        if profiler is not None:
            _logger.info("Using profiler.")

        main_task = asyncio.current_task()
        self._main_tasks.add(main_task)
        tasks = set()

        async def _loop(args):
            spec, full_path = build_fig_spec(
                    args.pop("fig"),
                    args.pop("path", None),
                    args.pop("opts", None)
                    )
            args["spec"] = spec
            args["full_path"] = full_path
            tab = await self._get_kaleido_tab()
            if profiler is not None and tab.tab.target_id not in profiler:
                profiler[tab.tab.target_id] = []
            t = asyncio.create_task(
                    self._render_task(
                        tab,
                        args = args,
                        error_log=error_log,
                        profiler=profiler)
                    )
            t.add_done_callback(
                    partial(
                        self._check_render_task,
                        full_path.name,
                        tab,
                        main_task
                        )
                    )
            tasks.add(t)
        try:
            if hasattr(generator, "__aiter__"): # is async iterable
                _logger.debug("Is async for")
                async for args in generator:
                    await _loop(args)
            else:
                _logger.debug("Is sync for")
                for args in generator:
                    await _loop(args)
            _logger.debug("awaiting tasks")
            await asyncio.gather(*tasks, return_exceptions=True)
        except:
            _logger.exception("Cleaning tasks after error.")
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise
        finally:
            self._main_tasks.remove(main_task)
