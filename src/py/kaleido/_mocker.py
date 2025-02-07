from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path
from pprint import pp

import logistro
import orjson

import kaleido

logistro.getLogger().setLevel(15)
_logger = logistro.getLogger(__name__)

# Extract jsons of mocks
test_dir = Path(__file__).resolve().parent.parent / "tests"
in_dir = test_dir / "mocks"
out_dir = test_dir / "renders"

scripts = [
    "https://cdn.plot.ly/plotly-3.0.0.min.js",
    "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js",
]


def _get_jsons_in_paths(path: str | Path) -> list[Path]:
    # Work with Paths and directories
    path = Path(path) if isinstance(path, str) else path

    if path.is_dir():
        return [path / a for a in path.glob("*.json")]
    else:
        return [path]


def _load_figures_from_paths(paths: list[Path]):
    # Set json
    for path in paths:
        if path.is_file():
            with path.open() as file:
                figure = orjson.loads(file.read())
                _logger.info(f"Yielding {path.stem}")
                yield {
                        "fig": figure,
                        "path": args.output / f"{path.stem}.{args.format}"
                        }
        else:
            raise RuntimeError(f"Path {path} is not a file.")


# Set the arguments
description = """kaleido_mocker will load up json files of plotly figs and export them.

If you set multiple process, -n, non-headless mode won't function well because
chrome will actually throttle tabs or windows/visibile- unless that tab/window
is headless.

The export of the program is a json object containing information about the execution.
"""

if "--headless" in sys.argv and "--no-headless" in sys.argv:
    raise ValueError(
        "Choose either '--headless' or '--no-headless'.",
    )

parser = argparse.ArgumentParser(
        add_help=True,
        parents=[logistro.parser],
        conflict_handler="resolve",
        description=description)

parser.add_argument(
    "--logistro-level",
    default="INFO",
    dest="log",
    help="Set the logging level (default INFO)",
)

parser.add_argument("--n", type=int, default=4, help="Number of tabs, default 4")

parser.add_argument(
    "--input",
    type=str,
    default=in_dir,
    help="Directory of mock file/s, default tests/mocks"
)

parser.add_argument(
    "--output",
    type=str,
    default=out_dir,
    help="Directory of mock file/s, default tests/renders"
)

parser.add_argument(
    "--format",
    type=str,
    default="png",
    help="png (default), pdf, jpg, webp, svg, json"
)

parser.add_argument(
    "--timeout",
    type=int,
    default=60,
    help="Set timeout in seconds for any 1 mock (default 60 seconds)"
)

parser.add_argument(
    "--headless",
    action="store_true",
    default=True,
    help="Set headless as True (default)",
)

parser.add_argument(
    "--no-headless", action="store_false", dest="headless", help="Set headless as False"
)


args = parser.parse_args()


# Function to process the images
async def _main(error_log = None, profiler = None):
    paths = _get_jsons_in_paths(args.input)
    async with kaleido.Kaleido(
        n=args.n, page_scripts=scripts, headless=args.headless, timeout=args.timeout
    ) as k:
        await k.write_fig_generate_all(
            _load_figures_from_paths(paths),
            error_log=error_log,
            profiler=profiler,
        )

def build_mocks():
    start = time.perf_counter()
    try:
        error_log = []
        profiler = {}
        asyncio.run(_main(error_log, profiler))
    finally:
        from operator import itemgetter

        for tab, tab_profile in profiler.items():
            profiler[tab] = sorted(
                tab_profile, key=itemgetter("duration"), reverse=True
            )

        elapsed = time.perf_counter() - start
        results = {
                "error_log": [str(log) for log in error_log],
                "profiles": profiler,
                "total_time": f"Time taken: {elapsed:.6f} seconds",
                "total_errors": len(error_log)
                }
        pp(results)


if __name__ == "__main__":
    build_mocks()
