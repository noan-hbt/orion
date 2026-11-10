"""Hybrid logical clock timestamps for the journal.

A timestamp combines physical milliseconds with a logical counter: it stays close to wall time
and never goes backwards, even when the system clock stalls or is set back. The string form
sorts lexicographically in timestamp order, so SQLite can order events by it directly.

Only the local half of the clock is kept (no `observe` of a remote timestamp): nothing in Orion
exchanges events between instances yet.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

_WALL_DIGITS = 15
_COUNTER_DIGITS = 6
_MAX_COUNTER = 16**_COUNTER_DIGITS - 1


@dataclass(frozen=True, slots=True, order=True)
class Timestamp:
    wall_ms: int
    counter: int
    node: str

    def encode(self) -> str:
        return f"{self.wall_ms:0{_WALL_DIGITS}d}.{self.counter:0{_COUNTER_DIGITS}x}.{self.node}"

    @classmethod
    def decode(cls, value: str) -> Timestamp:
        wall, counter, node = value.split(".", 2)
        return cls(int(wall), int(counter, 16), node)

    def __str__(self) -> str:
        return self.encode()


def _system_ms() -> int:
    return time.time_ns() // 1_000_000


class HybridClock:
    """Thread-safe clock for one node (one Orion instance)."""

    def __init__(self, node: str, clock_ms: Callable[[], int] | None = None) -> None:
        if not node or "." in node:
            raise ValueError("node id must be non-empty and must not contain '.'")
        self._node = node
        self._clock_ms = clock_ms or _system_ms
        self._lock = threading.Lock()
        self._wall = 0
        self._counter = 0

    @property
    def node(self) -> str:
        return self._node

    def now(self) -> Timestamp:
        with self._lock:
            physical = self._clock_ms()
            if physical > self._wall:
                self._wall, self._counter = physical, 0
            else:
                if self._counter >= _MAX_COUNTER:
                    raise OverflowError("HLC counter overflow")
                self._counter += 1
            return Timestamp(self._wall, self._counter, self._node)
