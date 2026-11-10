"""Projections: rebuilt from the journal alone, checkpointed with their state (R1.3)."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from telos.core.events import Event, NewEvent
from telos.core.journal import SqliteJournal
from telos.core.projections import ProjectionRunner, SqliteProjection
from tests.conftest import make_event


class WordCount(SqliteProjection):
    """Toy projection: words per source."""

    name = "word_count"
    version = 1
    schema = "CREATE TABLE words (source TEXT PRIMARY KEY, n INTEGER NOT NULL);"
    fail_on_seq: int | None = None

    def apply_event(self, db: sqlite3.Connection, event: Event) -> None:
        if event.seq == self.fail_on_seq:
            raise ValueError("boom")
        if event.kind == "note.added" and not event.redacted:
            n = len(str(event.payload["text"]).split())
            db.execute(
                "INSERT INTO words (source, n) VALUES (?, ?) "
                "ON CONFLICT(source) DO UPDATE SET n = n + excluded.n",
                (event.provenance.source, n),
            )

    async def counts(self) -> dict[str, int]:
        rows = await self._sql.run(lambda: self._sql.db.execute("SELECT * FROM words").fetchall())
        return {r[0]: r[1] for r in rows}


class WordCountV2(WordCount):
    version = 2
    schema = "CREATE TABLE words (source TEXT PRIMARY KEY, n INTEGER NOT NULL, extra TEXT);"


def note(source: str, text: str) -> NewEvent:
    return make_event("note.added", source=source, text=text)


async def test_a_destroyed_projection_is_rebuilt_identically(
    journal: SqliteJournal, tmp_path: Path
) -> None:
    await journal.append([note("a", "un deux trois"), note("b", "quatre"), make_event("other.x")])
    path = tmp_path / "words.sqlite3"
    async with WordCount(path) as projection:
        await ProjectionRunner(journal, [projection], batch=2).catch_up()
        before = await projection.snapshot()
    path.unlink()
    async with WordCount(path) as projection:
        assert await ProjectionRunner(journal, [projection]).catch_up() == 3
        assert await projection.snapshot() == before
        assert await projection.counts() == {"a": 3, "b": 1}


async def test_catch_up_resumes_after_restart_and_new_schema_rebuilds(
    journal: SqliteJournal, tmp_path: Path
) -> None:
    path = tmp_path / "words.sqlite3"
    await journal.append([note("a", "un deux")])
    async with WordCount(path) as projection:
        await ProjectionRunner(journal, [projection]).catch_up()
    await journal.append([note("a", "trois")])
    async with WordCount(path) as projection:
        assert await ProjectionRunner(journal, [projection]).catch_up() == 1  # only the new one
        assert await projection.counts() == {"a": 3}
    async with WordCountV2(path) as projection:
        assert await projection.checkpoint() == 0
        assert await ProjectionRunner(journal, [projection]).catch_up() == 2
        assert await projection.counts() == {"a": 3}


async def test_concurrent_catch_ups_apply_each_event_once_and_redaction_is_forgotten(
    journal: SqliteJournal, tmp_path: Path
) -> None:
    async with WordCount(tmp_path / "words.sqlite3") as projection:
        runner = ProjectionRunner(journal, [projection], batch=1)
        _, forget = await journal.append([note("a", "garde moi"), note("b", "oublie")])
        await asyncio.gather(runner.catch_up(), runner.catch_up(), runner.rebuild_all())
        assert await projection.counts() == {"a": 2, "b": 1}

        await journal.redact([forget.id], reason="forget b", actor="owner:main")
        await ProjectionRunner.rebuild_everywhere(journal)
        assert await projection.counts() == {"a": 2}
        assert await runner.verify() == []


async def test_a_failed_apply_stops_at_its_checkpoint_and_resumes(
    journal: SqliteJournal, tmp_path: Path
) -> None:
    async with WordCount(tmp_path / "words.sqlite3") as projection:
        projection.fail_on_seq = 2
        runner = ProjectionRunner(journal, [projection])
        await journal.append([note("a", w) for w in ("x", "y", "z")])
        with pytest.raises(ValueError, match="boom"):
            await runner.catch_up()
        assert await projection.checkpoint() == 1
        projection.fail_on_seq = None
        assert await runner.catch_up() == 2
        assert await projection.counts() == {"a": 3}
