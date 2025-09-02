from __future__ import annotations

from typing import TYPE_CHECKING

import logistro

_logger = logistro.getLogger(__name__)

if TYPE_CHECKING:
    from typing import Any

    import choreographer


def _make_console_logger(name, log):  # TODO(AJP) how do we use this
    """Create printer specifically for console events. Helper function."""

    async def console_printer(event):
        _logger.debug2(f"{name}:{event}")  # TODO(AJP): parse? stretch goal.
        log.append(str(event))

    return console_printer


class JavascriptLogger:
    log: list[Any]
    """A list of console outputs from the tab."""

    def __init__(self, tab: choreographer.Tab) -> None:
        self.log = []
        self.tab = tab

    def activate(self):
        self.tab.unsubscribe("Runtime.consoleAPICalled")
        self.tab.subscribe(
            "Runtime.consoleAPICalled",
            _make_console_logger("tab js console", self.log),
        )

    def reset(self):
        self.tab.unsubscribe("Runtime.consoleAPICalled")
        self.log = []
        self.tab.subscribe(
            "Runtime.consoleAPICalled",
            _make_console_logger("tab js console", self.log),
        )
