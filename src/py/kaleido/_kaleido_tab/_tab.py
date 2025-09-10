from __future__ import annotations

import base64
from typing import TYPE_CHECKING

import logistro

from . import _devtools_utils as _dtools
from . import _js_logger
from ._errors import _raise_error

if TYPE_CHECKING:
    import asyncio
    from pathlib import Path

    import choreographer as choreo

    from kaleido import _fig_tools


_TEXT_FORMATS = ("svg", "json")  # eps

_logger = logistro.getLogger(__name__)


def _subscribe_new(tab: choreo.Tab, event: str) -> asyncio.Future:
    """Create subscription to tab clearing old ones first: helper function."""
    new_future = tab.subscribe_once(event)
    while new_future.done():
        _logger.debug2(f"Clearing an old {event}")
        new_future = tab.subscribe_once(event)
    return new_future


class _KaleidoTab:
    """
    A Kaleido tab is a wrapped choreographer tab providing the functions we need.

    The choreographer tab can be accessed through the `self.tab` attribute.
    """

    tab: choreo.Tab
    """The underlying choreographer tab."""
    js_logger: _js_logger.JavascriptLogger
    """A log for recording javascript."""

    def __init__(self, tab, *, _stepper=False):
        """
        Create a new _KaleidoTab.

        Args:
            tab: the choreographer tab to wrap.

        """
        self.tab = tab
        self.js_logger = _js_logger.JavascriptLogger(self.tab)
        self._stepper = _stepper

    async def navigate(self, url: str | Path = ""):
        """
        Navigate to the kaleidofier script. This is effectively the real initialization.

        Args:
            url: Override the location of the kaleidofier script if necessary.

        """
        # Subscribe to event which will contain javascript engine ID (need it
        # for calling javascript functions)
        javascript_ready = _subscribe_new(self.tab, "Runtime.executionContextCreated")

        # Subscribe to event indicating page ready.
        page_ready = _subscribe_new(self.tab, "Page.loadEventFired")

        # Navigating page. This will trigger the above events.
        _logger.debug2(f"Calling Page.navigate on {self.tab}")
        _raise_error(await self.tab.send_command("Page.navigate", params={"url": url}))

        # Enabling page events (for page_ready- like all events, if already
        # ready, the latest will fire immediately)
        _logger.debug2(f"Calling Page.enable on {self.tab}")
        _raise_error(await self.tab.send_command("Page.enable"))

        # Enabling javascript events (for javascript_ready)
        _logger.debug2(f"Calling Runtime.enable on {self.tab}")
        _raise_error(await self.tab.send_command("Runtime.enable"))

        self._current_js_id = _dtools.get_js_id(await javascript_ready)

        await page_ready  # don't care result, ready is ready

        # this runs *after* page load because running it first thing
        # requires a couple extra lines
        self.js_logger.reset()

    # reload is truly so close to navigate
    async def reload(self):
        """Reload the tab, and set the javascript runtime id."""
        _logger.debug(f"Reloading tab {self.tab} with javascript.")

        javascript_ready = _subscribe_new(self.tab, "Runtime.executionContextCreated")

        page_ready = _subscribe_new(self.tab, "Page.loadEventFired")

        _logger.debug2(f"Calling Page.reload on {self.tab}")
        _raise_error(await self.tab.send_command("Page.reload"))

        self._current_js_id = _dtools.get_js_id(await javascript_ready)

        await page_ready

        self.js_logger.reset()

    async def _calc_fig(
        self,
        spec: _fig_tools.Spec,
        *,
        topojson: str | None = None,
        **_kwargs,
    ) -> bytes:
        _kwargs.pop("error_log", None)  # not used at the moment
        _kwargs.pop("profiler", None)  # not used at the moment

        # js script
        kaleido_js_fn = (
            r"function(spec, ...args)"
            r"{"
            r"return kaleido_scopes.plotly(spec, ...args).then(JSON.stringify);"
            r"}"
        )

        result = await _dtools.exec_js_fn(
            self.tab,
            self._current_js_id,
            kaleido_js_fn,
            spec,
            topojson,
            self._stepper,
        )
        _raise_error(result)

        # TODO(AJP): better define these error mechanics, is this a devtools
        # function or what
        # upon implementation of error, might not be necessary
        # to do these go-lang/c style returns
        # but we have to collect and associate
        # with the gather + profile
        # None-non return values are a problem
        # In general, need to better understand stuff here

        _logger.debug2(f"Result of function call: {result}")
        js_response, error = _dtools.check_kaleido_js_response(result)
        if error:
            raise error

        if (response_format := js_response.get("format")) == "pdf":
            img_raw, error = await _dtools.print_pdf(self.tab)
        else:
            img_raw = js_response.get("result")  # type: ignore[assignment]
        if error:
            raise error

        if response_format not in _TEXT_FORMATS:
            return base64.b64decode(img_raw)
        else:
            return str.encode(img_raw)
