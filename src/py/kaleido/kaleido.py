"""the kaleido module kaleido.py provides the main classes for the kaleido package."""

from __future__ import annotations

import asyncio
import base64
import json
import time
import traceback
import warnings
from collections.abc import Iterable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import choreographer as choreo
import logistro
from choreographer.errors import ChromeNotFoundError, DevtoolsProtocolError
from choreographer.utils import TmpDirectory

if TYPE_CHECKING:
    from typing import Any

from ._fig_tools import build_fig_spec

# Path of the page to use (kaleido-fier)
_PAGE_PATH = (Path(__file__).resolve().parent / "vendor" / "index.html").as_uri()
_TEXT_FORMATS = ("svg", "json")  # eps

_logger = logistro.getLogger(__name__)

# This annoying little global can be used to help debugging
# if set to True, will ask for user confirmation between each render
_stepper = False


# this is kinda public but undocumented
def set_stepper():
    """
    Cause kaleido require keypress between rendering and exporting graphs.

    If it is used with n>1, behavior is undefined.
    """
    global _stepper  # noqa: PLW0603
    _stepper = True


class ErrorEntry:
    """A simple object to record errors and context."""

    def __init__(self, name, error, javascript_log):
        """
        Construct an error entry.

        Args:
            name: the name of the image with the error
            error: the error object (from class BaseException)
            javascript_log: an array of entries from the javascript console

        """
        self.name = name
        self.error = error
        self.javascript_log = javascript_log

    def __str__(self):
        """Display the error object in a concise way."""
        ret = f"{self.name}:\n"
        e = self.error
        ret += " ".join(traceback.format_exception(type(e), e, e.__traceback__))
        ret += " javascript Log:\n"
        ret += "\n ".join(self.javascript_log)
        return ret


class KaleidoError(Exception):
    """An error to interpret errors from Kaleido's JS side."""

    def __init__(self, code, message):
        """
        Construct an error object.

        Args:
            code: the number code of the error.
            message: the message of the error.

        """
        super().__init__(message)
        self._code = code
        self._message = message

    def __str__(self):
        """Display the KaleidoError nicely."""
        return f"Error {self._code}: {self._message}"


class JavascriptError(RuntimeError):  # TODO(A): process better # noqa: TD003, FIX002
    """Used to report errors from javascript."""


def _make_printer(name):
    """Create event printer for generic events. Helper function."""

    async def print_all(response):
        _logger.debug2(f"{name}:{response}")

    return print_all


def _make_console_logger(name, log):
    """Create printer specifically for console events. Helper function."""

    async def console_printer(event):
        _logger.debug2(f"{name}:{event}")  # TODO(A): parse # noqa: TD003, FIX002
        log.append(str(event))

    return console_printer


def _check_error_ret(result):  # Utility
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
class _KaleidoTab:
    """
    A Kaleido tab is a wrapped choreographer tab providing the functions we need.

    The choreographer tab can be access through the `self.tab` attribute.
    """

    tab: choreo.Tab
    """The underlying choreographer tab."""

    javascript_log: list[Any]
    """A list of console outputs from the tab."""

    def __init__(self, tab):
        """
        Create a new _KaleidoTab.

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
            _make_console_logger("tab js console", self.javascript_log),
        )

    async def navigate(self, url: str | Path = ""):
        """
        Navigate to the kaleidofier script. This is effectively the real initialization.

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
        _check_error(await tab.send_command("Page.navigate", params={"url": url}))
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
                "Result {javascript_ready.result()}.",
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
                "Result {javascript_ready.result()}.",
            )
        await is_loaded
        self._regenerate_javascript_console()

    async def console_print(self, message: str) -> None:
        """
        Print something to the javascript console.

        Args:
            message: The thing to print.

        """
        jsfn = r"function()" r"{" f"console.log('{message}')" r"}"
        params = {
            "functionDeclaration": jsfn,
            "returnByValue": False,
            "userGesture": True,
            "awaitPromise": True,
            "executionContextId": self._current_js_id,
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
            profile["megabytes"] = size_mb

    async def _write_fig(  # noqa: C901 too many complexity
        self,
        spec,
        full_path,
        *,
        topojson=None,
        error_log=None,
        profiler=None,
    ):
        """
        Call the plotly renderer via javascript.

        Args:
            spec: the processed plotly figure
            full_path: the path to write the image too. if its a directory, we will try
                to generate a name. If the path contains an extension,
                "path/to/my_image.png", that extension will be the format used if not
                overridden in `opts`.
            opts: dictionary describing format, width, height, and scale of image
            topojson: topojsons are used to customize choropleths
            error_log: A supplied list, will be populated with `ErrorEntry`s
                       which can be converted to strings. Note, this is for
                       collections errors that have to do with plotly. They will
                       not be thrown. Lower level errors (kaleido, choreographer)
                       will still be thrown. If not passed, all errors raise.
            profiler: a supplied dictionary to collect stats about the operation

        """
        if profiler is not None:
            profile = {
                "name": full_path.name,
                "start": time.perf_counter(),
            }
        _logger.info(f"Value of stepper: {_stepper}")
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
        arguments = [{"value": spec}]
        arguments.append({"value": topojson if topojson else None})
        arguments.append({"value": _stepper})
        params = {
            "functionDeclaration": kaleido_jsfn,
            "arguments": arguments,
            "returnByValue": False,
            "userGesture": True,
            "awaitPromise": True,
            "executionContextId": execution_context_id,
        }

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
                _logger.error(f"Failed {full_path.name}", exc_info=e)
                return
            else:
                _logger.erroor(f"Raising error on {full_path.name}")
                raise e
        _logger.debug2(f"Result of function call: {result}")
        if _stepper:
            print(f"Image {full_path.name} was sent to browser")  # noqa: T201
            input("Press Enter to continue...")

        img = await self._img_from_response(result)
        if isinstance(img, BaseException):
            if profiler is not None:
                self._finish_profile(profile, img)
                profiler[tab.target_id].append(profile)
            if error_log is not None:
                error_log.append(
                    ErrorEntry(full_path.name, img, self.javascript_log),
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
            self._finish_profile(profile, e, full_path.stat().st_size / 1000000)
            profiler[tab.target_id].append(profile)

    async def _img_from_response(self, response):
        js_response = json.loads(response.get("result").get("result").get("value"))

        if js_response["code"] != 0:
            return KaleidoError(js_response["code"], js_response["message"])

        response_format = js_response.get("format")
        img = js_response.get("result")
        if response_format == "pdf":
            pdf_params = {
                "printBackground": True,
                "marginTop": 0.1,
                "marginBottom": 0.1,
                "marginLeft": 0.1,
                "marginRight": 0.1,
                "preferCSSPageSize": False,
                "pageRanges": "1",
            }
            pdf_response = await self.tab.send_command(
                "Page.printToPDF",
                params=pdf_params,
            )
            e = _check_error_ret(pdf_response)
            if e:
                return e
            img = pdf_response.get("result").get("data")
        # Base64 decode binary types
        if response_format not in _TEXT_FORMATS:
            img = base64.b64decode(img)
        else:
            img = str.encode(img)
        return img


class Kaleido(choreo.Browser):
    """Kaleido manages a set of image processors."""

    _tabs_ready: asyncio.Queue[_KaleidoTab]
    _background_render_tasks: set[asyncio.Task]
    # not really render tasks
    _main_tasks: set[asyncio.Task]

    async def close(self):
        """Close the browser."""
        if self.tmp_dir:
            self.tmp_dir.clean()
        _logger.info("Cancelling tasks.")
        for task in self._main_tasks:
            if not task.done():
                task.cancel()
        for task in self._background_render_tasks:
            if not task.done():
                task.cancel()
        _logger.info("Exiting Kaleido/Choreo")
        return await super().close()

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        """Close the browser."""
        _logger.info("Waiting for all cleanups to finish.")
        await asyncio.gather(*self._background_render_tasks, return_exceptions=True)
        _logger.info("Exiting Kaleido")
        return await super().__aexit__(exc_type, exc_value, exc_tb)

    def _generate_index(self, page_scripts):
        self.tmp_dir = TmpDirectory(path=Path(__file__).resolve().parent / "vendor")
        page = """
<!DOCTYPE html>
<html>
    <head>
        <style id="head-style"></style>
        <title>Kaleido-fier</title>
        <script>
          window.PlotlyConfig = {MathJaxConfig: 'local'}
        </script>
"""
        script_template = '\n        <script src="%s"></script>'
        footer = """
        <script src="../kaleido_scopes.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image"><img></body>
</html>
"""
        for script in page_scripts:
            page += script_template % script
        page += footer
        _logger.debug(page)
        with (self.tmp_dir.path / "index.html").open("w") as f:
            f.write(page)
        return (self.tmp_dir.path / "index.html").as_uri()

    def __init__(self, *args, **kwargs):  # noqa: D417 no args/kwargs in description
        """
        Initialize Kaleido, a `choreo.Browser` wrapper adding kaleido functionality.

        It takes all `choreo.Browser` args, plus some extra. The extra
        are listed, see choreographer for more documentation.

        Note: Chrome will throttle background tabs and windows, so non-headless
        multi-process configurations don't work well.

        Args:
            n: the number of separate processes (windows, not seen) to use.
            timeout: limit on any single render.
            width: width of window (headless only)
            height: height of window (headless only)
            page_scripts: a list of urls when building a plotly page instead
                          of the defaults.

        """
        self._background_render_tasks = set()
        self._main_tasks = set()
        self._tabs_ready = asyncio.Queue(maxsize=0)
        self._tmp_dir = None

        page_scripts = kwargs.pop("page_scripts", None)
        if page_scripts:
            self._index = self._generate_index(page_scripts)
        else:
            self._index = _PAGE_PATH
        self._timeout = kwargs.pop("timeout", 60)
        self._n = kwargs.pop("n", 1)
        self._height = kwargs.pop("height", None)
        self._width = kwargs.pop("width", None)
        if not kwargs.get("headless", True) and (self._height or self._width):
            warnings.warn(
                "Height and Width can only be used if headless=True, "
                "ignoring both sizes.",
                stacklevel=1,
            )
            self._height = None
            self._width = None

        try:
            super().__init__(*args, **kwargs)
        except ChromeNotFoundError:
            raise ChromeNotFoundError(
                "Versions 1.0.0 and higher of Kaleido do not include chrome by"
                "default. Earlier versions, we can be pinned, did but they were "
                "much smaller. Kaleido's dependency, choreographer, supplies a "
                "choreo_get_chrome CLI command as well as a `get_chrome()` and "
                "`get_chrome_sync()` function from "
                "`choreographer import cli as cli; cli.get_chrome()`",
            ) from ChromeNotFoundError

    async def _conform_tabs(self, tabs=None) -> None:
        if not tabs:
            tabs = list(self.tabs.values())
        _logger.info(f"Conforming {len(tabs)} to {self._index}")

        for i, tab in enumerate(tabs):
            n = f"tab-{i!s}"
            _logger.debug2(f"Subscribing * to tab: {tab}.")
            tab.subscribe("*", _make_printer(n + " event"))

        _logger.debug("Navigating all tabs")

        kaleido_tabs = [_KaleidoTab(tab) for tab in tabs]

        # A little hard to read because we don't have TaskGroup in this version
        tasks = [asyncio.create_task(tab.navigate(self._index)) for tab in kaleido_tabs]
        _logger.info("Waiting on all navigates")
        await asyncio.gather(*tasks)
        _logger.info("All navigates done, putting them all in queue.")
        for tab in kaleido_tabs:
            await self._tabs_ready.put(tab)
        _logger.debug("Tabs fully navigated/enabled/ready")

    async def populate_targets(self) -> None:
        """
        Override the browser populate_targets to ensure the correct page.

        Is called automatically during initialization, and should only be called
        once ever per object.
        """
        await super().populate_targets()
        await self._conform_tabs()
        needed_tabs = self._n - len(self.tabs)
        if needed_tabs < 0:
            raise RuntimeError("Did you set 0 or less tabs?")
        if not needed_tabs:
            return
        tasks = [
            asyncio.create_task(self._create_kaleido_tab()) for _ in range(needed_tabs)
        ]

        await asyncio.gather(*tasks)
        for tab in self.tabs.values():
            _logger.info(f"Tab ready: {tab.target_id}")

    async def _create_kaleido_tab(
        self,
    ) -> None:
        """
        Create a tab with the kaleido script.

        Returns:
            The kaleido-tab created.

        """
        tab = await super().create_tab(
            url="",
            width=self._width,
            height=self._height,
            window=True,
        )
        await self._conform_tabs([tab])

    async def _get_kaleido_tab(self) -> _KaleidoTab:
        """
        Retrieve an available tab from queue.

        Returns:
            A kaleido-tab from the queue.

        """
        _logger.info(f"Getting tab from queue (has {self._tabs_ready.qsize()})")
        tab = await self._tabs_ready.get()
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
        _logger.info(
            f"Putting tab {tab.tab.target_id[:4]} back (queue size: "
            f"{self._tabs_ready.qsize()}).",
        )
        await self._tabs_ready.put(tab)
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

    def _check_render_task(self, name, tab, main_task, error_log, task):
        if e := task.exception():
            if isinstance(e, asyncio.CancelledError):
                _logger.info(f"Something cancelled {name}.")
            _logger.error(f"Render Task Error In {name}- ", exc_info=e)
            if isinstance(e, (asyncio.TimeoutError, TimeoutError)) and error_log:
                error_log.append(
                    ErrorEntry(name, e, tab.javascript_log),
                )
            else:
                _logger.error("Cancelling all.")
                if not main_task.done():
                    main_task.cancel()
                raise e
        _logger.info(f"Returning {name} tab after render.")
        t = asyncio.create_task(self._return_kaleido_tab(tab))
        self._background_render_tasks.add(t)
        t.add_done_callback(partial(self._clean_tab_return_task, main_task))

    async def _render_task(self, tab, args, error_log=None, profiler=None):
        _logger.info(f"Posting a task for {args['full_path'].name}")
        if self._timeout:
            await asyncio.wait_for(
                tab._write_fig(  # noqa: SLF001 I don't want it documented, too complex for user
                    **args,
                    error_log=error_log,
                    profiler=profiler,
                ),
                self._timeout,
            )
        else:
            await tab._write_fig(  # noqa: SLF001 I don't want it documented, too complex for user
                **args,
                error_log=error_log,
                profiler=profiler,
            )
        _logger.info(f"Posted task ending for {args['full_path'].name}")

    async def write_fig(  # noqa: PLR0913, C901 (too many args, complexity)
        self,
        fig,
        path=None,
        opts=None,
        *,
        topojson=None,
        error_log=None,
        profiler=None,
    ):
        """
        Call the plotly renderer via javascript on first available tab.

        Args:
            fig: the plotly figure or an iterable of plotly figures
            path: the path to write the images to. if its a directory, we will try to
                generate a name. If the path contains an extension,
                "path/to/my_image.png", that extension will be the format used if not
                overridden in `opts`. If you pass a complete path (filename), for
                multiple figures, you will overwrite every previous figure.
            opts: dictionary describing format, width, height, and scale of image
            topojson: a link ??? TODO
            error_log: a supplied list, will be populated with `ErrorEntry`s
                       which can be converted to strings. Note, this is for
                       collections errors that have to do with plotly. They will
                       not be thrown. Lower level errors (kaleido, choreographer)
                       will still be thrown. If not passed, all errors raise.
            profiler: a supplied dictionary to collect stats about the operation
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
                    args={
                        "spec": spec,
                        "full_path": full_path,
                        "topojson": topojson,
                    },
                ),
                error_log=error_log,
                profiler=profiler,
            )
            t.add_done_callback(
                partial(
                    self._check_render_task,
                    full_path.name,
                    tab,
                    main_task,
                    error_log,
                ),
            )
            tasks.add(t)

        try:
            if hasattr(fig, "__aiter__"):  # is async iterable
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

    async def write_fig_generate_all(  # noqa: C901 too complex
        self,
        generator,
        *,
        error_log=None,
        profiler=None,
    ):
        """
        Equal to `write_fig` but allows the user to generate all arguments.

        Generator must yield dictionaries with keys:
        - fig: the plotly figure
        - path: (optional, string or pathlib.Path) the path
        - opts: (optional) dictionary with:
            - format (string)
            - scale (number)
            - height (number)
            - and width (number)
        - topojson: (optional) topojsons are used to customize choropleths

        Generators are good because, if rendering many images, one doesn't need to
        prerender them all. They can be rendered and yielded asynchronously.

        While `write_fig` can also take generators, but only for the figure.
        In this case, the generator will specify all render-related arguments.

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
                args.pop("opts", None),
            )
            args["spec"] = spec
            args["full_path"] = full_path
            tab = await self._get_kaleido_tab()
            if profiler is not None and tab.tab.target_id not in profiler:
                profiler[tab.tab.target_id] = []
            t = asyncio.create_task(
                self._render_task(
                    tab,
                    args=args,
                    error_log=error_log,
                    profiler=profiler,
                ),
            )
            t.add_done_callback(
                partial(
                    self._check_render_task,
                    full_path.name,
                    tab,
                    main_task,
                    error_log,
                ),
            )
            tasks.add(t)

        try:
            if hasattr(generator, "__aiter__"):  # is async iterable
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
