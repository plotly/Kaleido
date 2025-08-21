"""the kaleido module kaleido.py provides the main classes for the kaleido package."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlparse

import choreographer as choreo
import logistro
from choreographer.errors import ChromeNotFoundError
from choreographer.utils import TmpDirectory

from . import _utils
from ._fig_tools import _is_figurish, build_fig_spec
from ._kaleido_tab import _KaleidoTab
from ._page_generator import PageGenerator

_logger = logistro.getLogger(__name__)

# Show a warning if the installed Plotly version
# is incompatible with this version of Kaleido
_utils.warn_incompatible_plotly()


class Kaleido(choreo.Browser):
    _tabs_ready: asyncio.Queue[_KaleidoTab]
    _tab_requeue_tasks: set[asyncio.Task]
    _main_render_coroutines: set[asyncio.Task]
    # technically Tasks, user sees coroutines

    _total_tabs: int
    _html_tmp_dir: None | TmpDirectory

    ### KALEIDO LIFECYCLE FUNCTIONS ###

    def __init__(self, *args, **kwargs):
        self._tab_requeue_tasks = set()
        self._main_render_coroutines = set()
        self._tabs_ready = asyncio.Queue(maxsize=0)
        self._total_tabs = 0
        self._html_tmp_dir = None

        # Kaleido Config
        page = kwargs.pop("page_generator", None)
        self._timeout = kwargs.pop("timeout", 90)
        self._n = kwargs.pop("n", 1)
        if self._n <= 0:
            raise ValueError("Argument `n` must be greater than 0")
        self._plotlyjs = kwargs.pop("plotlyjs", None)
        self._mathjax = kwargs.pop("mathjax", None)

        # Diagnostic
        self._stepper = kwargs.pop("stepper", False)

        _logger.debug(f"Timeout: {self._timeout}")

        try:
            super().__init__(*args, **kwargs)
        except ChromeNotFoundError:
            raise ChromeNotFoundError(
                "Kaleido v1 and later requires Chrome to be installed. "
                "To install Chrome, use the CLI command `kaleido_get_chrome`, "
                "or from Python, use either `kaleido.get_chrome()` "
                "or `kaleido.get_chrome_sync()`.",
            ) from ChromeNotFoundError

        # not a lot of error detection here
        if page and isinstance(page, str) and Path(page).is_file():
            self._index = Path(page).as_uri()
        elif page and isinstance(page, str) and page.startswith("file://"):
            self._index = page
        elif page and hasattr(page, "is_file") and page.is_file():
            self._index = page.as_uri()
        elif page and not hasattr(page, "generate_index"):
            raise ValueError(
                "`page_generator argument` must be None, an existing file or "
                "an object with a generate_index function such as a "
                "kaleido.PageGenerator().",
            )
        else:
            self._html_tmp_dir = TmpDirectory(sneak=self.is_isolated())
            index = self._html_tmp_dir.path / "index.html"
            self._index = index.as_uri()
            if not page:
                page = PageGenerator(plotly=self._plotlyjs, mathjax=self._mathjax)
            with index.open("w") as f:
                f.write(page.generate_index())

        if not Path(urlparse(self._index).path).is_file():
            raise FileNotFoundError(f"{page} not found.")

    async def _conform_tabs(self, tabs) -> None:
        _logger.info(f"Conforming {len(tabs)} to {self._index}")

        for i, tab in enumerate(tabs):
            _logger.debug2(f"Subscribing * to tab: {tab}.")
            tab.subscribe("*", _utils.make_printer(f"tab-{i!s} event"))

        kaleido_tabs = [_KaleidoTab(tab, _stepper=self._stepper) for tab in tabs]

        await asyncio.gather(*(tab.navigate(self._index) for tab in kaleido_tabs))

        for tab in kaleido_tabs:
            self._total_tabs += 1
            await self._tabs_ready.put(tab)

    async def populate_targets(self) -> None:
        """
        Override the browser populate_targets to ensure the correct page.

        Is called automatically during initialization, and should only be called
        once ever per object.
        """
        await super().populate_targets()
        await self._conform_tabs(self.tabs.values())
        needed_tabs = self._n - len(self.tabs)
        if not needed_tabs:
            return

        await asyncio.gather(
            *(self._create_kaleido_tab() for _ in range(needed_tabs)),
        )

    async def close(self):
        """Close the browser."""
        if self._html_tmp_dir:
            self._html_tmp_dir.clean()

        # cancellation only happens if crash/early
        _logger.info("Cancelling tasks.")
        for task in self._main_render_coroutines:
            if not task.done():
                task.cancel()
        for task in self._tab_requeue_tasks:
            if not task.done():
                task.cancel()

        _logger.info("Exiting Kaleido/Choreo.")
        return await super().close()

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        """Close the browser."""
        _logger.info("Waiting for all cleanups to finish.")

        # render "tasks" are coroutines, so use is awaiting them
        await asyncio.gather(*self._tab_requeue_tasks, return_exceptions=True)

        _logger.info("Exiting Kaleido.")
        return await super().__aexit__(exc_type, exc_value, exc_tb)

    ### TAB MANAGEMENT FUNCTIONS ####

    async def _create_kaleido_tab(self) -> None:
        tab = await super().create_tab(
            url="",
            window=True,
        )
        await self._conform_tabs([tab])

    async def _get_kaleido_tab(self) -> _KaleidoTab:
        _logger.info(f"Getting tab from queue (has {self._tabs_ready.qsize()})")
        if not self._total_tabs:
            raise RuntimeError(
                "Before generating a figure, you must await `k.open()`.",
            )
        tab = await self._tabs_ready.get()
        _logger.info(f"Got {tab.tab.target_id[:4]}")
        return tab

    async def _return_kaleido_tab(self, tab) -> None:
        _logger.info(f"Reloading tab {tab.tab.target_id[:4]} before return.")
        await tab.reload()
        _logger.info(
            f"Putting tab {tab.tab.target_id[:4]} back (queue size: "
            f"{self._tabs_ready.qsize()}).",
        )
        await self._tabs_ready.put(tab)
        _logger.debug(f"{tab.tab.target_id[:4]} put back.")

    async def _create_render_task(self, tab, *args, **kwargs) -> asyncio.Task:
        _logger.info(f"Posting a task for {args['full_path'].name}")
        t = asyncio.create_task(
            asyncio.wait_for(
                tab._write_fig(  # noqa: SLF001
                    *args,
                    **kwargs,
                ),
                self._timeout,
            ),
        )

        # we just log any error but honestly it would be pretty fatal
        t.add_done_callback(
            lambda: self._tab_requeue_tasks.add(
                _utils.create_task_log_error(
                    self._return_kaleido_tab(tab),
                ),
            ),
        )
        _logger.info(f"Posted task ending for {args['full_path'].name}")
        return t

    ### API ###

    # also write_fig_from_dict
    async def write_fig_from_object(
        self,
        generator,  # what should we accept here
        *,
        cancel_on_error=False,
    ) -> None:
        """Temp."""
        main_task = asyncio.current_task()
        self._main_render_coroutines.add(main_task)
        tasks = set()

        try:
            async for args in _utils.ensure_async_iter(generator):
                spec, full_path = build_fig_spec(
                    args.get("fig"),
                    args.get("path", None),
                    args.get("opts", None),
                )
                topojson = args.get("topojson")

                tab = await self._get_kaleido_tab()

                t = self._create_render_task(
                    tab,
                    spec,
                    full_path,
                    topojson=topojson,
                )

                tasks.add(t)

            await asyncio.gather(*tasks, return_exceptions=not cancel_on_error)

        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            self._main_render_coroutines.remove(main_task)
            # return errors?

    async def write_fig(
        self,
        fig,
        path=None,
        opts=None,
        *,
        topojson=None,
    ) -> None:
        """Temp."""
        if _is_figurish(fig) or not isinstance(fig, Iterable):
            fig = [fig]
        else:
            _logger.debug(f"Is iterable {type(fig)}")

        async def _temp_generator():
            async for f in _utils.ensure_async_iter(fig):
                yield {
                    "fig": f,
                    "path": path,
                    "opts": opts,
                    "topojson": topojson,
                }

        return await self.write_fig_from_object(
            generator=_temp_generator(),
        )
