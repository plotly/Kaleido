"""the kaleido module kaleido.py provides the main classes for the kaleido package."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict
from urllib.parse import unquote, urlparse

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

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any, List, Tuple, TypeVar, Union, ValuesView

    from typing_extensions import NotRequired, Required, TypeAlias

    from . import _fig_tools

    T = TypeVar("T")
    AnyIterable: TypeAlias = Union[Iterable[T], AsyncIterable[T]]  # not runtime

    # union of sized iterables since 3.8 doesn't have & operator
    # Iterable & Sized
    Listish: TypeAlias = Union[Tuple[T], List[T], ValuesView[T]]


class Kaleido(choreo.Browser):
    tabs_ready: asyncio.Queue[_KaleidoTab]
    _tab_requeue_tasks: set[asyncio.Task]
    _main_render_coroutines: set[asyncio.Task]
    # technically Tasks, user sees coroutines

    _total_tabs: int
    _html_tmp_dir: None | TmpDirectory

    ### KALEIDO LIFECYCLE FUNCTIONS ###

    def __init__(  # noqa: PLR0913
        self,
        *args: Any,  # does choreographer take args?
        n: int = 1,
        timeout: int | None = 90,
        page_generator: None | PageGenerator | str | Path = None,
        plotlyjs: str | Path | None = None,
        mathjax: str | Path | None = None,
        stepper: bool = False,
        **kwargs: Any,
    ) -> None:
        self._tab_requeue_tasks = set()
        self._main_render_coroutines = set()
        self.tabs_ready = asyncio.Queue(maxsize=0)
        self._total_tabs = 0
        self._html_tmp_dir = None

        # Kaleido Config
        page = page_generator
        self._timeout = timeout
        self._n = n
        self._stepper = stepper
        self._plotlyjs = plotlyjs
        self._mathjax = mathjax

        # Diagnostic
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
        # do this during open because it requires close
        self._saved_page_arg = page

    async def open(self):
        """Build temporary file if we need one."""
        page = self._saved_page_arg
        del self._saved_page_arg

        if isinstance(page, str):
            if page.startswith(r"file://") and Path(unquote(urlparse(page).path)):
                self._index = page
            elif Path(page).is_file():
                self._index = Path(page).as_uri()
            else:
                raise FileNotFoundError(f"{page} does not exist.")
        elif isinstance(page, Path):
            if page.is_file():
                self._index = page.as_uri()
            else:
                raise FileNotFoundError(f"{page!s} does not exist.")
        else:
            self._tmp_dir = TmpDirectory(sneak=self.is_isolated())
            index = self._tmp_dir.path / "index.html"
            self._index = index.as_uri()
            if not page:
                page = PageGenerator(plotly=self._plotlyjs, mathjax=self._mathjax)
            page.generate_index(index)
        await super().open()

    async def _conform_tabs(self, tabs: Listish[choreo.Tab] | None = None) -> None:
        if not tabs:
            tabs = self.tabs.values()
        _logger.info(f"Conforming {len(tabs)} to {self._index}")
        for i, tab in enumerate(tabs):
            _logger.debug2(f"Subscribing * to tab: {tab}.")
            tab.subscribe("*", _utils.event_printer(f"tab-{i!s}: Event Dump:"))

        kaleido_tabs = [_KaleidoTab(tab, _stepper=self._stepper) for tab in tabs]

        await asyncio.gather(*(tab.navigate(self._index) for tab in kaleido_tabs))

        for ktab in kaleido_tabs:
            self._total_tabs += 1
            await self.tabs_ready.put(ktab)

    async def populate_targets(self) -> None:
        """
        Override the browser populate_targets to ensure the correct page.

        Is called automatically during initialization, and should only be called
        once ever per object.
        """
        await super().populate_targets()
        await self._conform_tabs()
        needed_tabs = self._n - len(self.tabs)
        if not needed_tabs:
            return

        await asyncio.gather(
            *(self._create_kaleido_tab() for _ in range(needed_tabs)),
        )

    async def close(self) -> None:
        """Close the browser."""
        await super().close()

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

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
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
        _logger.info(f"Getting tab from queue (has {self.tabs_ready.qsize()})")
        if not self._total_tabs:
            raise RuntimeError(
                "Before generating a figure, you must await `k.open()`.",
            )
        tab = await self.tabs_ready.get()
        _logger.info(f"Got {tab.tab.target_id[:4]}")
        return tab

    async def _return_kaleido_tab(self, tab: _KaleidoTab) -> None:
        _logger.info(f"Reloading tab {tab.tab.target_id[:4]} before return.")
        await tab.reload()
        _logger.info(
            f"Putting tab {tab.tab.target_id[:4]} back (queue size: "
            f"{self.tabs_ready.qsize()}).",
        )
        await self.tabs_ready.put(tab)
        _logger.debug(f"{tab.tab.target_id[:4]} put back.")

    #### WE'RE HERE

    def _create_render_task(
        self,
        tab: _KaleidoTab,
        spec: _fig_tools.Spec,
        full_path: Path,
        **kwargs: Any,
    ) -> asyncio.Task:
        _logger.info(f"Posting a task for {full_path.name}")
        t: asyncio.Task = asyncio.create_task(
            asyncio.wait_for(
                tab._write_fig(  # noqa: SLF001
                    spec,
                    full_path,
                    **kwargs,
                ),
                self._timeout,
            ),
        )
        # create_task_log_error is a create_task helper, set and forget
        # to create a task and add a post-run action which checks for
        # errors and logs them. this pattern is the best i've found
        # but somehow its still pretty distressing
        t.add_done_callback(
            lambda _f: self._tab_requeue_tasks.add(
                _utils.create_task_log_error(
                    self._return_kaleido_tab(tab),
                ),
            ),
        )
        _logger.info(f"Posted task ending for {full_path.name}")
        return t

    ### API ###

    class FigureGenerator(TypedDict):
        fig: Required[_fig_tools.Figurish]
        path: NotRequired[None | str | Path]
        opts: NotRequired[_fig_tools.LayoutOpts | None]

    # also write_fig_from_dict
    async def write_fig_from_object(
        self,
        generator: FigureGenerator,  # what should we accept here
        *,
        cancel_on_error=False,
    ) -> None:
        """Temp."""
        if main_task := asyncio.current_task():
            self._main_render_coroutines.add(main_task)
        tasks: set[asyncio.Task] = set()

        try:
            async for args in _utils.ensure_async_iter(generator):
                spec, full_path = build_fig_spec(
                    args.get("fig"),
                    args.get("path", None),
                    args.get("opts", None),
                )
                topojson = args.get("topojson")

                tab = await self._get_kaleido_tab()

                t: asyncio.Task = self._create_render_task(
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
            if main_task:
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
        if _is_figurish(fig) or not isinstance(fig, (Iterable, AsyncIterable)):
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
