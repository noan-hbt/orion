"""Event versions: the journal is never rewritten, so old events are read in today's shape.

An event is stored as it was written, with the version of its kind at that time. When a kind's
payload changes shape (a field renamed, a value split in two), the journal is not touched: a
function turning version N into N+1 is added to the kind's list of upcasters, and every read
applies the ones the event has not been through. A kind renamed as a whole goes in `renamed`;
its events are read under the new name.

Rules for an upcaster: pure (same input, same output, no clock, no I/O), total (it accepts every
payload of its version, including ones missing optional fields), and never deleted once
shipped: a journal written years ago still needs it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

type Payload = dict[str, Any]
type Upcaster = Callable[[Payload], Payload]


class NewerEventError(ValueError):
    """An event written by a newer Telos than this one."""


@dataclass
class EventVersions:
    upcasters: dict[str, list[Upcaster]] = field(default_factory=dict[str, list[Upcaster]])
    """kind → [v1 → v2, v2 → v3, …]. The current version of a kind is 1 + len(its list)."""

    renamed: dict[str, str] = field(default_factory=dict[str, str])
    """old kind → new kind, read as the new kind (then upcast from the new kind's version 1)."""

    def version_of(self, kind: str) -> int:
        """The version a payload of `kind` is written at today."""
        return 1 + len(self.upcasters.get(kind, ()))

    def upcast(self, kind: str, version: int, payload: Payload) -> tuple[str, Payload]:
        """An event as written (`kind`, `version`, `payload`), in today's shape."""
        if version < 1:
            raise ValueError(f"event of kind {kind!r} has no valid version ({version})")
        if kind in self.renamed:
            kind, version = self.renamed[kind], 1  # its old versions are the new kind's first
        steps = self.upcasters.get(kind, [])
        if version > len(steps) + 1:
            raise NewerEventError(
                f"event of kind {kind!r} is version {version}, newer than this Telos knows "
                f"({len(steps) + 1}): run the newer Telos, or restore the journal from a backup"
            )
        for step in steps[version - 1 :]:
            payload = step(dict(payload))
        return kind, payload


VERSIONS = EventVersions()
"""The versions of every event kind Telos writes. Modules add their upcasters here."""
