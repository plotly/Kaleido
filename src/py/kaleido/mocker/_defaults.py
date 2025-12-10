from __future__ import annotations

import multiprocessing
from pathlib import Path

import logistro

_logger = logistro.getLogger(__name__)


width = [700, 200, 1000]  # first value in main default if not parameterized
height = [500, 200, 1000]
scale = [1, 0.5, 2]
extension = [
    "png",
    "pdf",
    "jpg",
    "webp",
    "svg",
    "json",
]

# use itertools.product

# Number of CPUS
cpus = multiprocessing.cpu_count()

# Default Directories
test_dir = Path(__file__).resolve().parent.parent.parent / "integration_tests"
in_dir = test_dir / "mocks"
out_dir = test_dir / "renders"
