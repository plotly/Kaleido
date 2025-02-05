from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import logistro

import baile

logistro.getLogger().setLevel(11)
_logger = logistro.getLogger(__name__)

# Extract jsons of mocks
in_dir = Path(__file__).resolve().parent / "mocks"
out_dir = Path(__file__).resolve().parent / "renders"


def _get_jsons_in_paths(path: str | Path) -> list[Path]:
    # Work with Paths and directories
    path = Path(path) if isinstance(path, str) else path

    if path.is_dir():
        return [ path / a for a in path.glob("*.json") ]
    else:
        return [ path ]

def _load_figures_from_paths(paths: list[Path]):
    # Set json
    for path in paths:
        if path.is_file():
            with path.open() as file:
                figure = json.load(file) # TODO use faster json reader
                _logger.info(f"Yielding {path.stem}")
                yield { "fig": figure, "path": args.output / f"{path.stem}.png" }
        else:
            raise RuntimeError(f"Path {path} is not a file.")

# Set the arguments
parser = argparse.ArgumentParser()
parser.add_argument(
        "--n",
        type=int,
        default=4,
        help="Number of tabs"
        )

parser.add_argument(
        "--input",
        type=str,
        default=in_dir,
        help="Directory of mock file/s"
        )

parser.add_argument(
        "--output",
        type=str,
        default=out_dir,
        help="Directory of mock file/s"
        )

parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Set headless as True",
        )

parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="Set headless as False"
        )

args = parser.parse_args()

# Function to process the images
async def _main():
    paths = _get_jsons_in_paths(args.input)
    async with baile.Kaleido(n=args.n, headless=args.headless) as k:
        error_log = []
        await k.write_fig_generate_all(
                _load_figures_from_paths(paths),
                error_log=error_log
                )
    for error in error_log:
        print(error)
    print(f"Num of errors: {len(error_log)})")

def build_mocks():
    start = time.perf_counter()
    try:
        asyncio.run(_main())
    finally:
        end = time.perf_counter()
        elapsed = end - start
        print(f"Time taken: {elapsed:.6f} seconds")

if __name__ == "__main__":
    build_mocks()
