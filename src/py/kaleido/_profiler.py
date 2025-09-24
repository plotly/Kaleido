from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from ._utils import fig_tools

    Event = str


class WriteCall:
    name: str
    renders: list[RenderTaskProfile]

    __slots__ = tuple(__annotations__)

    def __init__(self, name: str):
        self.name = name
        self.renders = []


class RenderTaskProfile:
    info: dict[str, Any]  # literal?
    error: None | BaseException
    js_log: list[str]
    profile_log: ProfileLog
    data_in_size: int | None
    data_out_size: int | None

    __slots__ = tuple(__annotations__)

    def __init__(
        self,
        spec: fig_tools.Spec,
        full_path: Path | None,
        tab_id: str,
    ) -> None:
        self.info = {}
        self.error = None
        self.js_log = []
        self.profile_log = ProfileLog()
        self.data_in_size = None  # need to get this from choreographer
        self.data_out_size = None

        self.info.update(
            {k: v for k, v in spec.items() if k != "data"},
        )
        self.info["path"] = full_path
        self.info["tab"] = tab_id


class ProfileLog:
    _logs: dict[Event, float]

    __slots__ = tuple(__annotations__)

    def __init__(self) -> None:
        self._logs = {}

    def tick(self, name: str) -> None:
        self._logs[name] = time.perf_counter()

    def get_logs(self) -> dict[Event, float]:
        return self._logs
