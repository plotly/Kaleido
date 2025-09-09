"""the kaleido module kaleido.py provides the main classes for the kaleido package."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

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

    class FigureDict(TypedDict):
        """The type a generator returns for `write_fig_from_object`."""

        fig: Required[_fig_tools.Figurish]
        path: NotRequired[None | str | Path]
        opts: NotRequired[_fig_tools.LayoutOpts | None]
        topojson: NotRequired[None | str]


class Kaleido(choreo.Browser):
    """
    The Kaleido object provides a browser to render and write plotly figures.

    It provides methods to render said figures, and manages any number of tabs
    in a work queue. Start it one of a few equal ways:

    async with Kaleido() as k:
        ...

    # or

    k = await Kaleido()
    ...
    await k.close()

    # or

    k = Kaleido()
    await k.open()
    ...
    await.k.close()
    """

    tabs_ready: asyncio.Queue[_KaleidoTab]
    """A queue of tabs ready to process a kaleido figure."""
    _tab_requeue_tasks: set[asyncio.Task]
    _main_render_coroutines: set[asyncio.Task]
    # technically Tasks, user sees coroutines

    _total_tabs: int
    _html_tmp_dir: None | TmpDirectory

    ### KALEIDO LIFECYCLE FUNCTIONS ###

    def __init__(  # noqa: PLR0913
        self,
        *args: Any,  # TODO(AJP): does choreographer take args?
        n: int = 1,
        timeout: int | None = 90,
        page_generator: None | PageGenerator | str | Path = None,
        plotlyjs: str | Path | None = None,  # TODO(AJP): with page generator
        mathjax: str | Path | None = None,  # TODO(AJP): with page generator?
        stepper: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Create a new Kaleido process for rendering plotly figures.

        Args:
            *args (Any):
                Passed through to underlying choreographer.Browser()
            n (int, optional):
                Number of processors to use (parallelization). Defaults to 1.

            timeout (int | None, optional):
                Number of seconds to wait to render any one image. None for no
                timeout. Defaults to 90.

            page_generator (None | PageGenerator | str | Path, optional):
                A PageGenerator object can be used for deep customization of the
                plotly template page. This is for development use. You can also
                pass a string or path directly to an index.html, or any object
                with a `generate_index()->str function that prints an HTML
                ppage. Defaults to None.

            plotlyjs (str | Path | None, optional):
                A path or URL to a plotly.js file. Defaults to None- which means
                to use the plotly.js included with your version of plotly.py or
                if not installed, the latest version available via CDN.

            mathjax (str | Path | None, optional):
                A path or URL to a mathjax.js file. If false, mathjax is
                disabled. Defaults to None- which means to use version 2.35 via
                CDN.

            stepper (bool, optional):
                A diagnostic tool that will ask the user to press enter between
                rendering each image. Only useful if also used with
                `headless=False`. See below. Defaults to False.

            **kwargs (Any):
                Additional keyword arguments passed through to the underlying
                Choreographer.browser constructor. Notable options include,
                `headless=False` (show window), `enable_sandbox=True` (turn on
                sandboxing), and `enable_gpu=True` which will allow use of the
                GPU. The defaults for these options are True, False, False
                respectively.

        """
        self._tab_requeue_tasks = set()
        # State variables
        self._main_render_coroutines = set()
        self.tabs_ready = asyncio.Queue(maxsize=0)
        self._total_tabs = 0 # tabs properly registered
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
                "or from Python, use either `await kaleido.get_chrome()` "
                "or `kaleido.get_chrome_sync()`.",
            ) from None  # overwriting the error entirely.

        # save this for open() because it requires close()
        self._saved_page_arg = page

    async def open(self):
        """Build page and temporary file if we need one, then opens browser."""
        page = self._saved_page_arg
        del self._saved_page_arg

        if isinstance(page, (Path, str)):
            if (_p := _utils.get_path(page)).is_file():
                self._index = _p.as_uri()
            else:
                raise FileNotFoundError(f"{page!s} does not exist.")
        elif not page or hasattr(page, "generate_index"):
            self._tmp_dir = TmpDirectory(sneak=self.is_isolated())
            index = self._tmp_dir.path / "index.html"
            self._index = index.as_uri()
            if not page:
                page = PageGenerator(plotly=self._plotlyjs, mathjax=self._mathjax)
            with index.open("w") as f:  # is blocking but ok
                f.write(page.generate_index())
        else:
            raise TypeError(
                "page_generator must be one of: None, a"
                " PageGenerator, or a file path to an index.html.",
            )
        await super().open()

    async def _create_kaleido_tab(self) -> None:
        tab = await super().create_tab(
            url="",
            window=True,
        )
        await self._conform_tabs([tab])

    async def _conform_tabs(self, tabs: Listish[choreo.Tab] | None = None) -> None:
        if not tabs:
            tabs = self.tabs.values()
        _logger.info(f"Conforming {len(tabs)} to {self._index}")
        for i, tab in enumerate(tabs):
            _logger.debug2(f"Subscribing * to tab: {tab}.")
            tab.subscribe("*", _utils.event_printer(f"tab-{i!s}: Event Dump:"))

        kaleido_tabs = [_KaleidoTab(tab, _stepper=self._stepper) for tab in tabs]
        # TODO(AJP): why doesn't stepper use the global?

        await asyncio.gather(*(tab.navigate(self._index) for tab in kaleido_tabs))

        for ktab in kaleido_tabs:
            self._total_tabs += 1
            await self.tabs_ready.put(ktab)

    async def populate_targets(self) -> None:
        """
        Override the browser populate_targets to ensure the correct page.

        Is called automatically during initialization, and should only be called
        once.
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

        # a weak solution to chaining tasks
        # maybe consider an async closure instead
        # avoids try/except....
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

    # also write_fig_from_dict
    async def write_fig_from_object(
        self,
        generator: AnyIterable[FigureDict], # TODO: must take a FigureDict alone
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
        fig: _fig_tools.Figurish,
        path: None | Path | str = None,
        opts: None | _fig_tools.LayoutOpts = None,
        *,
        topojson: str | None = None,
    ) -> None:
        """Temp."""
        if not isinstance(fig, (Iterable, AsyncIterable)):
            fig = [fig]

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
