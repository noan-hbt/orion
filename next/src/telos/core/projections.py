"""Projections: derived state built by replaying the journal.

A projection must be a pure function of the events it has seen: dropping its state and
replaying the journal from the start has to rebuild exactly the same state (D81). That property
is what makes state reconstructible and forgetting verifiable: after a redaction, a rebuild
leaves nothing of what was erased.

Each projection's checkpoint (last applied sequence) is persisted next to its state by the
projection itself, so applying an event and advancing the checkpoint happen atomically.

A projection kept on disk (`SqliteProjection`) declares the version of its schema. When the
code's version differs from the file's, the file is not migrated: its tables are dropped and
the journal is replayed into the new ones. The journal is the truth; the projection is a cache.
"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
import sqlite3
import weakref
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Protocol, Self

from pydantic import BaseModel

from telos.core.events import Event
from telos.core.sqlite import SqliteWorker, dump

log = logging.getLogger(__name__)


class EventSource(Protocol):
    """What a runner needs from the journal."""

    async def read(self, after_seq: int = 0, limit: int = 1000) -> list[Event]: ...


class Projection(Protocol):
    @property
    def name(self) -> str:
        """Unique among the projections of a runner."""
        ...

    async def checkpoint(self) -> int:
        """Last journal sequence applied (0 if none)."""
        ...

    async def apply(self, event: Event) -> None:
        """Apply one event and advance the checkpoint to `event.seq`, atomically."""
        ...

    async def reset(self) -> None:
        """Drop all derived state and set the checkpoint back to 0."""
        ...


def snapshot(value: Any, _seen: frozenset[int] = frozenset()) -> Any:
    """A projection's state as plain, comparable data: what a rebuild must give back.

    A projection kept outside Python objects (in SQLite) gives its own with an async
    `snapshot()`; this one reads the attributes of the others."""
    if isinstance(value, str | int | float | bool | None | Enum):
        return value
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    if id(value) in _seen:
        return "<cycle>"
    seen = _seen | {id(value)}
    if isinstance(value, dict):
        items: dict[Any, Any] = value  # pyright: ignore[reportUnknownVariableType]
        pairs = ((repr(snapshot(k, seen)), snapshot(v, seen)) for k, v in items.items())
        return sorted(pairs, key=repr)
    if isinstance(value, set | frozenset):
        members: frozenset[Any] = frozenset(value)  # pyright: ignore[reportUnknownArgumentType]
        return sorted((snapshot(v, seen) for v in members), key=repr)
    if isinstance(value, list | tuple):
        sequence: list[Any] = list(value)  # pyright: ignore[reportUnknownArgumentType]
        return [snapshot(v, seen) for v in sequence]
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: snapshot(getattr(value, f.name), seen) for f in dataclasses.fields(value)}
    if isinstance(value, BaseModel):
        return snapshot(value.model_dump(), seen)
    if hasattr(value, "__dict__"):
        return {k: snapshot(v, seen) for k, v in sorted(vars(value).items())}
    return repr(value)


async def state_of(projection: Projection) -> Any:
    custom = getattr(projection, "snapshot", None)
    if custom is not None:
        return snapshot(await custom())
    return snapshot(projection)


class ProjectionRunner:
    """Keeps a set of projections caught up with the journal."""

    _by_journal: ClassVar[weakref.WeakKeyDictionary[Any, list[ProjectionRunner]]] = (
        weakref.WeakKeyDictionary()
    )
    """Every runner made on each journal, kept as long as the journal lives, even when its
    creator dropped it: a redaction rebuilds them all, and the test suite verifies them all at
    the end of every test (D81)."""

    def __init__(
        self, journal: EventSource, projections: Sequence[Projection], batch: int = 500
    ) -> None:
        names = [p.name for p in projections]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate projection names: {names}")
        self._journal = journal
        self._projections = list(projections)
        self._batch = batch
        self._lock = asyncio.Lock()
        """One catch-up or rebuild at a time: two reading the same cursor would apply the same
        events twice, and a rebuild must not reset state under a catch-up."""
        ProjectionRunner._by_journal.setdefault(journal, []).append(self)

    @property
    def journal(self) -> EventSource:
        return self._journal

    @property
    def projections(self) -> list[Projection]:
        return list(self._projections)

    async def catch_up(self) -> int:
        """Apply every pending event to every projection. Returns the number of applications."""
        applied = 0
        async with self._lock:
            for projection in self._projections:
                applied += await self._catch_up_one(projection)
        return applied

    async def rebuild(self, name: str) -> int:
        """Reset one projection and replay the whole journal into it."""
        projection = self._find(name)
        async with self._lock:
            return await self._rebuild(projection)

    async def rebuild_all(self) -> int:
        """Every projection reset and replayed: after a redaction, nothing keeps what was
        forgotten."""
        applied = 0
        async with self._lock:
            for projection in self._projections:
                applied += await self._rebuild(projection)
        return applied

    @classmethod
    async def rebuild_everywhere(cls, journal: EventSource) -> int:
        """Every projection of every runner on `journal` in this process, rebuilt: after a
        redaction, no part of Telos keeps what was forgotten, not only the one that forgot."""
        applied = 0
        for runner in cls.on(journal):
            applied += await runner.rebuild_all()
        return applied

    @classmethod
    def on(cls, journal: EventSource) -> list[ProjectionRunner]:
        """Every runner made on `journal`."""
        return list(cls._by_journal.get(journal, []))

    async def verify(self) -> list[str]:
        """Rebuild each projection and compare it with what it was. Returns the names of those
        that came back different: their state does not depend on the journal alone."""
        different: list[str] = []
        async with self._lock:
            for projection in self._projections:
                await self._catch_up_one(projection)  # a live one may lag behind the journal
                before = await state_of(projection)
                await self._rebuild(projection)
                if await state_of(projection) != before:
                    different.append(projection.name)
        return different

    async def _rebuild(self, projection: Projection) -> int:
        await projection.reset()
        log.info("projection rebuild: %s", projection.name)
        return await self._catch_up_one(projection)

    async def _catch_up_one(self, projection: Projection) -> int:
        cursor = await projection.checkpoint()
        applied = 0
        while True:
            events = await self._journal.read(cursor, self._batch)
            if not events:
                return applied
            for event in events:
                try:
                    await projection.apply(event)
                except Exception:
                    # Stop this projection at the failing event; it resumes from its checkpoint.
                    log.exception(
                        "projection %s failed to apply event seq=%d kind=%s",
                        projection.name,
                        event.seq,
                        event.kind,
                    )
                    raise
                cursor = event.seq
                applied += 1

    def _find(self, name: str) -> Projection:
        for projection in self._projections:
            if projection.name == name:
                return projection
        raise KeyError(f"unknown projection: {name}")


_STATE_TABLE = "projection_state"


class SqliteProjection(ABC):
    """A projection stored in its own SQLite file, with its checkpoint and schema version.

    Subclasses set `name`, `version` and `schema` (the `CREATE` statements of their tables) and
    implement `apply_event`, which runs inside the transaction that also advances the
    checkpoint. Reads go through `self._sql.run`.
    """

    name: ClassVar[str]
    version: ClassVar[int]
    """Schema version. Bump it whenever `schema` or the meaning of a column changes: the file
    is then dropped and rebuilt from the journal."""
    schema: ClassVar[str]

    def __init__(self, path: Path | str) -> None:
        self._sql = SqliteWorker(path, f"projection-{self.name}")

    async def open(self) -> None:
        await self._sql.open()
        await self._sql.run(self._open_sync)

    async def close(self) -> None:
        await self._sql.close()

    @property
    def closed(self) -> bool:
        return self._sql.closed

    async def __aenter__(self) -> Self:
        await self.open()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    @abstractmethod
    def apply_event(self, db: sqlite3.Connection, event: Event) -> None:
        """Apply one event to the tables. Runs on the projection's thread, in a transaction."""

    async def checkpoint(self) -> int:
        return await self._sql.run(self._checkpoint_sync)

    async def apply(self, event: Event) -> None:
        await self._sql.run(self._apply_sync, event)

    async def reset(self) -> None:
        await self._sql.run(self._reset_sync)

    async def snapshot(self) -> dict[str, list[tuple[object, ...]]]:
        return await self._sql.run(lambda: dump(self._sql.db, self._tables_sync()))

    # --- synchronous internals, always run on the projection's thread ---

    def _open_sync(self) -> None:
        stored = int(self._sql.db.execute("PRAGMA user_version").fetchone()[0])
        if stored != self.version:
            if stored:
                log.info(
                    "projection %s: schema %d -> %d, rebuilding", self.name, stored, self.version
                )
            self._reset_sync()

    def _reset_sync(self) -> None:
        db = self._sql.db
        # The version is cleared first and written last: a crash in between leaves a file
        # whose version does not match, so the next open resets it again.
        db.execute("PRAGMA user_version = 0")
        for table in self._tables_sync():
            db.execute(f"DROP TABLE {table}")
        db.execute(f"DROP TABLE IF EXISTS {_STATE_TABLE}")
        db.executescript(self.schema)
        db.execute(f"CREATE TABLE {_STATE_TABLE} (checkpoint INTEGER NOT NULL)")
        db.execute(f"INSERT INTO {_STATE_TABLE} (checkpoint) VALUES (0)")
        db.execute(f"PRAGMA user_version = {int(self.version)}")

    def _tables_sync(self) -> tuple[str, ...]:
        rows = self._sql.db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' AND name != ? ORDER BY name",
            (_STATE_TABLE,),
        )
        return tuple(r[0] for r in rows)

    def _checkpoint_sync(self) -> int:
        return int(self._sql.db.execute(f"SELECT checkpoint FROM {_STATE_TABLE}").fetchone()[0])

    def _apply_sync(self, event: Event) -> None:
        with self._sql.transaction() as db:
            self.apply_event(db, event)
            db.execute(f"UPDATE {_STATE_TABLE} SET checkpoint = ?", (event.seq,))
