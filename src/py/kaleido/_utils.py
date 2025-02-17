import asyncio
import traceback
from functools import partial


async def to_thread(func, *args, **kwargs):
    _loop = asyncio.get_running_loop()
    fn = partial(func, *args, **kwargs)
    await _loop.run_in_executor(None, fn)


class ErrorEntry:
    """A simple object to record errors and context."""

    def __init__(self, name, error, javascript_log):
        """
        Construct an error entry.

        Args:
            name: the name of the image with the error
            error: the error object (from class BaseException)
            javascript_log: an array of entries from the javascript console

        """
        self.name = name
        self.error = error
        self.javascript_log = javascript_log

    def __str__(self):
        """Display the error object in a concise way."""
        ret = f"{self.name}:\n"
        e = self.error
        ret += " ".join(traceback.format_exception(type(e), e, e.__traceback__))
        ret += " javascript Log:\n"
        ret += "\n ".join(self.javascript_log)
        return ret
