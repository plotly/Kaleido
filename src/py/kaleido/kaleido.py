"""the kaleido module kaleido.py provides the main classes for the kaleido package."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast, overload

import choreographer as choreo
import logistro
from choreographer.errors import ChromeNotFoundError
from choreographer.utils import TmpDirectory

from . import _fig_tools, _path_tools, _utils
from ._kaleido_tab import _KaleidoTab
from ._page_generator import PageGenerator

_logger = logistro.getLogger(__name__)

# Show a warning if the installed Plotly version
# is incompatible with this version of Kaleido
_utils.warn_incompatible_plotly()

if TYPE_CHECKING:
    from types import TracebackType
    from typing import (
        Any,
        AsyncGenerator,
        List,
        Literal,
        Tuple,
        TypeVar,
        Union,
        ValuesView,
    )

    from typing_extensions import NotRequired, Required, TypeAlias

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
        # State variables
        self._main_render_coroutines = set()
        self.tabs_ready = asyncio.Queue(maxsize=0)
        self._total_tabs = 0  # tabs properly registered
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
            self._html_tmp_dir = TmpDirectory(sneak=self.is_isolated())
            index = self._html_tmp_dir.path / "index.html"
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
        if self._html_tmp_dir:
            _logger.debug(f"Cleaning up {self._html_tmp_dir}")
            self._html_tmp_dir.clean()
        else:
            _logger.debug("No kaleido._html_tmp_dir to clean up.")

        await super().close()

        # cancellation only happens if crash/early
        _logger.info("Cancelling tasks.")
        for task in self._main_render_coroutines:
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

        await asyncio.gather(*self._main_render_coroutines, return_exceptions=True)

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

    async def _render_task(
        self,
        spec: _fig_tools.Spec,
        write_path: Path | None,
        **kwargs: Any,
    ) -> None | bytes:
        tab = await self._get_kaleido_tab()

        try:
            img_bytes = await asyncio.wait_for(
                tab._calc_fig(  # noqa: SLF001
                    spec,
                    **kwargs,
                ),
                self._timeout,
            )
            if write_path:
                await _utils.to_thread(write_path.write_bytes, img_bytes)
                return None
            else:
                return img_bytes

        finally:
            await self._return_kaleido_tab(tab)

    ### API ###
    @overload
    async def write_fig_from_object(
        self,
        generator: AnyIterable[FigureDict],
        *,
        cancel_on_error: bool = False,
        _write: Literal[False],
    ) -> bytes: ...

    @overload
    async def write_fig_from_object(
        self,
        generator: AnyIterable[FigureDict],
        *,
        cancel_on_error: Literal[True],
        _write: Literal[True] = True,
    ) -> None: ...

    @overload
    async def write_fig_from_object(
        self,
        generator: AnyIterable[FigureDict],
        *,
        cancel_on_error: Literal[False] = False,
        _write: Literal[True] = True,
    ) -> tuple[Exception]: ...

    @overload
    async def write_fig_from_object(
        self,
        generator: AnyIterable[FigureDict],
        *,
        cancel_on_error: bool,
        _write: Literal[True] = True,
    ) -> tuple[Exception] | None: ...

    async def write_fig_from_object(
        self,
        generator: AnyIterable[FigureDict],  # TODO: must take a FigureDict alone
        *,
        cancel_on_error=False,
        _write: bool = True,  # backwards compatibility!
    ) -> None | bytes | tuple[Exception]:
        """Temp."""
        if not _write:
            cancel_on_error = True
        if main_task := asyncio.current_task():
            self._main_render_coroutines.add(main_task)
        tasks: set[asyncio.Task] = set()

        try:
            async for fig_arg in _utils.ensure_async_iter(generator):
                spec = _fig_tools.coerce_for_js(
                    fig_arg.get("fig"),
                    fig_arg.get("path", None),
                    fig_arg.get("opts", None),
                )

                full_path = _path_tools.determine_path(
                    fig_arg.get("path", None),
                    spec["data"],
                    spec["format"],  # should just take spec
                )

                t: asyncio.Task = asyncio.create_task(
                    self._render_task(
                        spec=spec,
                        write_path=full_path if _write else None,  # bwrds - compat!
                        topojson=fig_arg.get("topojson"),
                    ),
                )
                tasks.add(t)

            res = await asyncio.gather(*tasks, return_exceptions=not cancel_on_error)
            if not _write:
                return cast("bytes", res[0])
            elif cancel_on_error:
                return None
            else:
                return cast("tuple[Exception]", tuple(r for r in res if r))

        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            if main_task:
                self._main_render_coroutines.remove(main_task)

    async def write_fig(
        self,
        fig: _fig_tools.Figurish,
        path: None | Path | str = None,
        opts: None | _fig_tools.LayoutOpts = None,
        *,
        topojson: str | None = None,
        cancel_on_error: bool = False,
    ) -> tuple[Exception] | None:
        """Temp."""
        if _fig_tools.is_figurish(fig) or not isinstance(
            fig,
            (Iterable, AsyncIterable),
        ):
            fig = [fig]

        async def _temp_generator() -> AsyncGenerator[FigureDict, None]:
            async for f in _utils.ensure_async_iter(fig):
                yield {
                    "fig": f,
                    "path": path,
                    "opts": opts,
                    "topojson": topojson,
                }

        generator = cast("AsyncIterable[FigureDict]", _temp_generator())
        return await self.write_fig_from_object(
            generator=generator,
            cancel_on_error=cancel_on_error,
        )

    async def calc_fig(
        self,
        fig: _fig_tools.Figurish,
        opts: None | _fig_tools.LayoutOpts = None,
        *,
        topojson: str | None = None,
    ) -> bytes:
        """Temp."""

        async def _temp_generator():
            yield {
                "fig": fig,
                "opts": opts,
                "topojson": topojson,
            }

        return await self.write_fig_from_object(
            generator=_temp_generator(),
            cancel_on_error=True,
            _write=False,
        )
