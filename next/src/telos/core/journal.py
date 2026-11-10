"""The journal: Telos's append-only source of truth.

Events are never updated nor deleted, and the database itself refuses it (triggers). The only
mutation is redaction, used to honour "forget this": the payload is erased, the row stays (so
sequence numbers and causal links remain intact), and a `journal.redacted` event records what
was erased and why.

Each event is stored with the version of its kind when it was written; reads bring it to
today's shape (`telos.core.upcast`), so changing a payload never means rewriting history.

SQLite runs in WAL mode with a single writer. All blocking calls go through a dedicated worker
thread so the asyncio loop never blocks on disk.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import cast

from telos.core.events import Event, NewEvent, Provenance, Trust
from telos.core.hlc import HybridClock
from telos.core.sqlite import SqliteWorker
from telos.core.upcast import VERSIONS, EventVersions

REDACTED_KIND = "journal.redacted"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq            INTEGER PRIMARY KEY,
    id             TEXT NOT NULL UNIQUE,
    hlc            TEXT NOT NULL,
    kind           TEXT NOT NULL,
    version        INTEGER NOT NULL,
    payload        TEXT NOT NULL,
    source         TEXT NOT NULL,
    actor          TEXT NOT NULL,
    agent          TEXT,
    derived_from   TEXT NOT NULL,
    trust          INTEGER NOT NULL,
    agent_id       TEXT,
    thread_id      TEXT,
    causation_id   TEXT,
    correlation_id TEXT,
    redacted       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS events_agent ON events(agent_id);
CREATE INDEX IF NOT EXISTS events_thread ON events(thread_id);
CREATE INDEX IF NOT EXISTS events_correlation ON events(correlation_id);

CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'the journal is append-only'); END;

CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE OF
    seq, id, hlc, kind, version, source, actor, agent, derived_from, trust,
    agent_id, thread_id, causation_id, correlation_id ON events
BEGIN SELECT RAISE(ABORT, 'the journal is append-only'); END;

CREATE TRIGGER IF NOT EXISTS events_only_redaction BEFORE UPDATE OF payload, redacted ON events
WHEN NEW.payload != '{}' OR NEW.redacted != 1
BEGIN SELECT RAISE(ABORT, 'the journal is append-only: only redaction erases a payload'); END;
"""

_COLUMNS = (
    "seq, id, hlc, kind, version, payload, source, actor, agent, derived_from, trust, "
    "agent_id, thread_id, causation_id, correlation_id, redacted"
)


class SqliteJournal:
    """One instance per database file; it is the single writer."""

    def __init__(self, path: Path, clock: HybridClock, versions: EventVersions = VERSIONS) -> None:
        self._clock = clock
        self._versions = versions
        self._sql = SqliteWorker(path, "journal", _SCHEMA)
        self._appended = asyncio.Condition()

    async def open(self) -> None:
        await self._sql.open()

    async def close(self) -> None:
        await self._sql.close()

    async def __aenter__(self) -> SqliteJournal:
        await self.open()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def append(self, events: Sequence[NewEvent]) -> list[Event]:
        """Append `events` atomically: all of them, or none."""
        if not events:
            return []
        stored = await self._sql.run(self._append_sync, list(events))
        await self._notify()
        return stored

    async def read(self, after_seq: int = 0, limit: int = 1000) -> list[Event]:
        return await self._sql.run(self._read_sync, after_seq, limit)

    async def get(self, event_id: str) -> Event | None:
        return await self._sql.run(self._get_sync, event_id)

    async def last_seq(self) -> int:
        return await self._sql.run(self._last_seq_sync)

    async def redact(self, event_ids: Sequence[str], reason: str, actor: str) -> Event:
        """Erase the payloads of `event_ids`, keep their rows, and journal why."""
        stored = await self._sql.run(self._redact_sync, list(event_ids), reason, actor)
        await self._notify()
        return stored

    async def follow(self, after_seq: int = 0, batch: int = 500) -> AsyncIterator[Event]:
        """Yield every event after `after_seq`, then keep waiting for new ones. Never ends."""
        cursor = after_seq
        while True:
            async with self._appended:
                events = await self.read(cursor, batch)
                if not events:
                    await self._appended.wait()
                    continue
            for event in events:
                cursor = event.seq
                yield event

    async def _notify(self) -> None:
        async with self._appended:
            self._appended.notify_all()

    # --- synchronous internals, always run on the journal thread ---

    def _event_from_row(self, row: sqlite3.Row) -> Event:
        kind, payload = row["kind"], json.loads(row["payload"])
        if not row["redacted"]:  # an erased payload has no shape left to bring up to date
            kind, payload = self._versions.upcast(kind, row["version"], payload)
        return Event(
            seq=row["seq"],
            id=row["id"],
            hlc=row["hlc"],
            kind=kind,
            payload=payload,
            provenance=Provenance(
                source=row["source"],
                actor=row["actor"],
                agent=row["agent"],
                derived_from=tuple(json.loads(row["derived_from"])),
            ),
            trust=Trust(row["trust"]),
            agent_id=row["agent_id"],
            thread_id=row["thread_id"],
            causation_id=row["causation_id"],
            correlation_id=row["correlation_id"],
            redacted=bool(row["redacted"]),
        )

    def _insert(self, db: sqlite3.Connection, new: NewEvent) -> Event:
        hlc = self._clock.now().encode()
        cur = db.execute(
            f"INSERT INTO events ({_COLUMNS.removeprefix('seq, ')}) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
            (
                new.id,
                hlc,
                new.kind,
                self._versions.version_of(new.kind),
                json.dumps(new.payload, separators=(",", ":"), sort_keys=True),
                new.provenance.source,
                new.provenance.actor,
                new.provenance.agent,
                json.dumps(list(new.provenance.derived_from)),
                int(new.trust),
                new.agent_id,
                new.thread_id,
                new.causation_id,
                new.correlation_id,
            ),
        )
        # sqlite always sets lastrowid after an INSERT into a rowid table.
        return Event(**new.model_dump(), seq=cast(int, cur.lastrowid), hlc=hlc)

    def _append_sync(self, events: list[NewEvent]) -> list[Event]:
        with self._sql.transaction() as db:
            return [self._insert(db, new) for new in events]

    def _read_sync(self, after_seq: int, limit: int) -> list[Event]:
        rows = self._sql.db.execute(
            f"SELECT {_COLUMNS} FROM events WHERE seq > ? ORDER BY seq LIMIT ?",
            (after_seq, limit),
        )
        return [self._event_from_row(r) for r in rows]

    def _get_sync(self, event_id: str) -> Event | None:
        row = self._sql.db.execute(
            f"SELECT {_COLUMNS} FROM events WHERE id = ?", (event_id,)
        ).fetchone()
        return self._event_from_row(row) if row else None

    def _last_seq_sync(self) -> int:
        row = self._sql.db.execute("SELECT COALESCE(MAX(seq), 0) FROM events").fetchone()
        return int(row[0])

    def _redact_sync(self, event_ids: list[str], reason: str, actor: str) -> Event:
        if not event_ids:
            raise ValueError("nothing to redact")
        with self._sql.transaction() as db:
            placeholders = ",".join("?" * len(event_ids))
            rows = db.execute(f"SELECT id FROM events WHERE id IN ({placeholders})", event_ids)
            missing = sorted(set(event_ids) - {r[0] for r in rows})
            if missing:
                raise KeyError(f"unknown event ids: {missing}")
            db.executemany(
                "UPDATE events SET payload = '{}', redacted = 1 WHERE id = ?",
                [(i,) for i in event_ids],
            )
            marker = NewEvent(
                kind=REDACTED_KIND,
                payload={"event_ids": sorted(event_ids), "reason": reason},
                provenance=Provenance(source="journal:redaction", actor=actor),
                trust=Trust.SYSTEM,
            )
            return self._insert(db, marker)
