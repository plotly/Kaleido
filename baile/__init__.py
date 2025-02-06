"""Kaleido provides to convert plotly figures into various image formats."""

from choreographer.cli import get_chrome, get_chrome_sync

from .kaleido import Kaleido

__all__ = [
    "Kaleido",
    "get_chrome",
    "get_chrome_sync",
    "write_fig",
    "write_fig_generate_all",
]


async def write_fig(  # noqa: PLR0913 (too many args, complexity)
    fig,
    path=None,
    opts=None,
    *,
    topojson=None,
    mapbox_token=None,
    error_log=None,
    profiler=None,
    n=1,
):
    """
    Write a plotly figure(s) to a file.

    A convenience wrapper for `Kaleido.write_fig` which starts a `Kaleido`.
    It takes one additional argument, `n`, which can be used to set the number
    of processes.

    See documentation for `Kaleido.write_fig`.

    """
    async with Kaleido(n=n) as k:
        await k.write_fig(
            fig,
            path=path,
            opts=opts,
            topojson=topojson,
            mapbox_token=mapbox_token,
            error_log=error_log,
            profiler=profiler,
        )


async def write_fig_generate_all(
    generator,
    *,
    error_log=None,
    profiler=None,
    n=1,
):
    """
    Write a plotly figure(s) to a file.

    A convenience wrapper for `Kaleido.write_fig_generate_all` which starts a `Kaleido`.
    It takes one additional argument, `n`, which can be used to set the number
    of processes.

    See documentation for `Kaleido.write_fig_generate_all`.

    """
    async with Kaleido(n=n) as k:
        await k.write_fig_generate_all(
            generator, error_log=error_log, profiler=profiler, n=n
        )
