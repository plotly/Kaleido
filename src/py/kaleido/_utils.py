from __future__ import annotations

import asyncio
import warnings
from functools import partial
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse
from urllib.request import url2pathname

import logistro
from packaging.version import Version

_logger = logistro.getLogger(__name__)

if TYPE_CHECKING:
    from typing import Any, Callable, Coroutine


def event_printer(name: str) -> Callable[[Any], Coroutine[Any, Any, None]]:
    """Return function that prints whatever argument received."""

    async def print_all(response: Any) -> None:
        _logger.debug2(f"{name!s}:{response!s}")

    return print_all


def _clean_error(t: asyncio.Task) -> None:
    """Check a task to avoid "task never awaited" errors."""
    if t.cancelled():
        _logger.error(f"{t} cancelled.")
    elif (exc := t.exception()) is not None:
        _logger.error(f"{t} raised error.", exc_info=exc)


def create_task_log_error(coroutine) -> asyncio.Task:
    """Create a task and assign a callback to log its errors."""
    t = asyncio.create_task(coroutine)
    t.add_done_callback(_clean_error)
    return t


def ensure_async_iter(obj):
    """Convert any iterable to an async iterator."""
    if hasattr(obj, "__aiter__"):
        return obj

    it = iter(obj)

    class _AIter:
        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(it)
            except StopIteration:
                raise StopAsyncIteration  # noqa: B904

    return _AIter()


async def to_thread(func, *args, **kwargs):
    """Polyfill `asyncio.to_thread()`."""
    _loop = asyncio.get_running_loop()
    fn = partial(func, *args, **kwargs)
    await _loop.run_in_executor(None, fn)


def warn_incompatible_plotly():
    """
    Check if installed Plotly version (if any) is compatible with this Kaleido version.

    If not, display a warning.
    """
    try:
        min_compatible_plotly_version = Version("6.1.1")
        installed_plotly_version = Version(version("plotly"))
        installed_kaleido_version = Version(version("kaleido"))
        if installed_plotly_version < min_compatible_plotly_version:
            warnings.warn(
                "\n\n"
                f"Warning: You have Plotly version {installed_plotly_version}, "
                "which is not compatible with this version of "
                f"Kaleido ({installed_kaleido_version}).\n\n"
                "This means that static image generation (e.g. `fig.write_image()`) "
                "will not work.\n\n"
                f"Please upgrade Plotly to version {min_compatible_plotly_version} "
                "or greater, or downgrade Kaleido to version 0.2.1.\n\n"
                "You can however, use the Kaleido API directly which will work "
                "with your plotly version. `kaleido.write_fig(...)`, for example. "
                "Please see the kaleido documentation."
                "\n",
                UserWarning,
                stacklevel=3,
            )
    except PackageNotFoundError:
        # If Plotly is not installed, there's nothing to worry about
        pass
    # ruff: noqa: BLE001
    except Exception as e:
        # If another error occurs, log it but do not raise
        # Since this compatibility check is just a convenience,
        # we don't want to block the whole library if there's an issue
        _logger.info("Error while checking Plotly version.", exc_info=e)


def get_path(p: str | Path) -> Path:
    if isinstance(p, Path):
        return p
    elif not isinstance(p, str):
        raise TypeError("Path should be a string or `pathlib.Path` object.")

    parsed = urlparse(str(p))

    return Path(
        url2pathname(parsed.path) if parsed.scheme.startswith("file") else p,
    )


def is_httpish(p: str) -> bool:
    return urlparse(str(p)).scheme.startswith("http")
