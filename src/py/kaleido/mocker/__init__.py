"""Mocker is an integration-test utility."""

from __future__ import annotations

import asyncio
import time
from random import sample
from typing import TYPE_CHECKING

import logistro

import kaleido

from . import _utils
from ._args import args

if TYPE_CHECKING:
    from pathlib import Path

_logger = logistro.getLogger(__name__)


def random_config(paths: list[Path]) -> list[Path]:
    """Select a portion of possible paths."""
    if args.random > len(paths):
        raise ValueError(
            f"Input discover {len(paths)} paths, but a sampling of"
            f"{args.random} was asked for.",
        )
    paths = sample(paths, args.random)


# Function to process the images
async def _main():
    paths = _utils.get_jsons_in_paths(args.input)
    if args.random:
        paths = random_config(paths)

    async with kaleido.Kaleido(
        page_generator=kaleido.PageGenerator(force_cdn=True),
        n=args.n,
        headless=args.headless,
        timeout=args.timeout,
    ) as k:
        await k.write_fig_from_object(
            _utils.load_figures_from_paths(paths),
            stepper=args.stepper,
            cancel_on_error=args.fail_fast,
        )


def main():
    """[project.scripts] expects to call a function, not a module."""
    start = time.perf_counter()
    try:
        asyncio.run(_main())
    finally:
        elapsed = time.perf_counter() - start


if __name__ == "__main__":
    main()
