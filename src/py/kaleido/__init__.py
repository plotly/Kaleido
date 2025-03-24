"""
Kaleido is a library for generating static images from Plotly figures.

Please see the README.md for more information and a quickstart.
"""

import asyncio
import queue
from threading import Thread

from choreographer.cli import get_chrome, get_chrome_sync

from ._page_generator import PageGenerator
from .kaleido import Kaleido

__all__ = [
    "Kaleido",
    "PageGenerator",
    "calc_fig",
    "calc_fig_sync",
    "get_chrome",
    "get_chrome_sync",
    "write_fig",
    "write_fig_from_object",
    "write_fig_from_object_sync",
    "write_fig_sync",
]


async def calc_fig(
    fig,
    path=None,
    opts=None,
    *,
    topojson=None,
):
    """
    Return binary for plotly figure.

    A convenience wrapper for `Kaleido.calc_fig()` which starts a `Kaleido` and
    executes the `calc_fig()`.

    See documentation for `Kaleido.calc_fig()`.

    """
    async with Kaleido(n=1) as k:
        return await k.calc_fig(
            fig,
            path=path,
            opts=opts,
            topojson=topojson,
        )


async def write_fig(  # noqa: PLR0913 (too many args, complexity)
    fig,
    path=None,
    opts=None,
    *,
    topojson=None,
    error_log=None,
    profiler=None,
    n=1,
):
    """
    Write a plotly figure(s) to a file.

    A convenience wrapper for `Kaleido.write_fig()` which starts a `Kaleido` and
    executes the `write_fig()`.
    It takes one additional argument, `n`, which can be used to set the number
    of processes.

    See documentation for `Kaleido.write_fig()`.

    """
    async with Kaleido(n=n) as k:
        await k.write_fig(
            fig,
            path=path,
            opts=opts,
            topojson=topojson,
            error_log=error_log,
            profiler=profiler,
        )


async def write_fig_from_object(
    generator,
    *,
    error_log=None,
    profiler=None,
    n=1,
):
    """
    Write a plotly figure(s) to a file.

    A convenience wrapper for `Kaleido.write_fig_from_object()` which starts a
    `Kaleido` and executes the `write_fig_from_object()`
    It takes one additional argument, `n`, which can be used to set the number
    of processes.

    See documentation for `Kaleido.write_fig_from_object()`.

    """
    async with Kaleido(n=n) as k:
        await k.write_fig_from_object(
            generator,
            error_log=error_log,
            profiler=profiler,
        )


def _async_thread_run(func, args, kwargs):
    q = queue.Queue(maxsize=1)

    def run(*args, **kwargs):
        # func is a closure
        try:
            q.put(asyncio.run(func(*args, **kwargs)))
        except BaseException as e:  # noqa: BLE001
            q.put(e)

    t = Thread(target=run, args=args, kwargs=kwargs)
    t.start()
    t.join()
    res = q.get()
    if isinstance(res, BaseException):
        raise res
    else:
        return res


def calc_fig_sync(*args, **kwargs):
    """Call `calc_fig` but blocking."""
    return _async_thread_run(calc_fig, args=args, kwargs=kwargs)


def write_fig_sync(*args, **kwargs):
    """Call `write_fig` but blocking."""
    _async_thread_run(write_fig, args=args, kwargs=kwargs)


def write_fig_from_object_sync(*args, **kwargs):
    """Call `write_fig_from_object` but blocking."""
    _async_thread_run(write_fig_from_object, args=args, kwargs=kwargs)
