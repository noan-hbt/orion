"""The journal: append-only, redactable, versioned (R1.2)."""

from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest

from telos.core.events import NewEvent, Provenance, Trust, derive_trust
from telos.core.hlc import HybridClock, Timestamp
from telos.core.ids import UlidGenerator
from telos.core.journal import REDACTED_KIND, SqliteJournal
from telos.core.upcast import EventVersions, NewerEventError


def event(kind: str = "test.happened", **payload: Any) -> NewEvent:
    return NewEvent(
        kind=kind,
        payload=payload,
        provenance=Provenance(source="test:1", actor="owner:main"),
        trust=Trust.OWNER,
    )


@pytest.fixture
async def journal(tmp_path: Path) -> AsyncIterator[SqliteJournal]:
    async with SqliteJournal(tmp_path / "j.sqlite3", HybridClock("t")) as j:
        yield j


async def test_events_come_back_whole_and_in_order_after_reopen(tmp_path: Path) -> None:
    path = tmp_path / "j.sqlite3"
    scoped = NewEvent(
        kind="message.received",
        payload={"text": "salut", "nested": {"a": [1, 2]}},
        provenance=Provenance(
            source="telegram:9", actor="agent:a1", agent="a1", derived_from=("x",)
        ),
        trust=Trust.THIRD_PARTY,
        agent_id="a1",
        thread_id="th1",
        correlation_id="flow",
    )
    async with SqliteJournal(path, HybridClock("t")) as j:
        stored = await j.append([scoped, *(event(n=i) for i in range(4))])
    async with SqliteJournal(path, HybridClock("t")) as j:
        read = await j.read()
        assert read == stored
        assert await j.get(scoped.id) == stored[0]
        assert await j.read(after_seq=2, limit=2) == stored[2:4]
    assert [e.seq for e in read] == sorted(e.seq for e in read)
    assert [Timestamp.decode(e.hlc) for e in read] == sorted(Timestamp.decode(e.hlc) for e in read)


async def test_a_batch_is_appended_whole_or_not_at_all(journal: SqliteJournal) -> None:
    first = event()
    await journal.append([first])
    with pytest.raises(sqlite3.IntegrityError):
        await journal.append([event(n=1), first])  # duplicate id: the whole batch rolls back
    assert await journal.last_seq() == 1


async def test_nothing_can_update_or_delete_an_event(tmp_path: Path) -> None:
    path = tmp_path / "j.sqlite3"
    async with SqliteJournal(path, HybridClock("t")) as j:
        [stored] = await j.append([event(body="x")])
    db = sqlite3.connect(path)
    for sql in (
        'UPDATE events SET payload = \'{"body":"y"}\'',
        "UPDATE events SET kind = 'other.kind'",
        "UPDATE events SET redacted = 0",
        "DELETE FROM events",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute(sql)
    db.close()
    async with SqliteJournal(path, HybridClock("t")) as j:
        assert await j.read() == [stored]


async def test_redaction_erases_the_payload_keeps_the_row_and_says_why(
    journal: SqliteJournal,
) -> None:
    keep, forget = await journal.append([event(body="ok"), event(body="secret")])
    with pytest.raises(KeyError):
        await journal.redact([forget.id, "nope"], reason="r", actor="owner:main")
    assert await journal.get(forget.id) == forget  # an unknown id changes nothing

    marker = await journal.redact([forget.id], reason="owner asked", actor="owner:main")
    assert marker.kind == REDACTED_KIND
    assert marker.payload == {"event_ids": [forget.id], "reason": "owner asked"}
    erased = await journal.get(forget.id)
    assert erased is not None and erased.redacted and erased.payload == {}
    assert erased.seq == forget.seq and erased.provenance == forget.provenance
    assert await journal.get(keep.id) == keep


async def test_old_events_are_read_in_todays_shape_without_rewriting_them(tmp_path: Path) -> None:
    path = tmp_path / "j.sqlite3"
    versions = EventVersions()
    async with SqliteJournal(path, HybridClock("t"), versions) as j:
        [old, erased] = await j.append(
            [event("place.seen", name="Gare"), event("place.seen", name="Maison")]
        )
        await j.redact([erased.id], "forget", "owner:main")

    # Later, `name` becomes `place`, then the kind is renamed.
    versions.upcasters["place.visited"] = [lambda p: {"place": p.pop("name"), **p}]
    versions.renamed["place.seen"] = "place.visited"
    async with SqliteJournal(path, HybridClock("t"), versions) as j:
        read = {e.id: e for e in await j.read()}
        assert read[old.id].kind == "place.visited"
        assert read[old.id].payload == {"place": "Gare"}
        assert read[erased.id].payload == {}  # an erased payload is not upcast

    db = sqlite3.connect(path)  # what is on disk did not change
    assert db.execute("SELECT payload FROM events WHERE id = ?", (old.id,)).fetchone() == (
        '{"name":"Gare"}',
    )
    db.close()


async def test_an_event_from_a_newer_telos_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "j.sqlite3"
    async with SqliteJournal(path, HybridClock("t"), EventVersions({"x.y": [lambda p: p]})) as j:
        await j.append([event("x.y")])
    async with SqliteJournal(path, HybridClock("t"), EventVersions()) as j:
        with pytest.raises(NewerEventError):
            await j.read()


async def test_follow_yields_the_backlog_then_new_events(journal: SqliteJournal) -> None:
    await journal.append([event(n=0)])
    seen: list[int] = []

    async def consume() -> None:
        async for e in journal.follow():
            seen.append(e.payload["n"])
            if len(seen) == 3:
                return

    consumer = asyncio.create_task(consume())
    await asyncio.sleep(0.05)
    await journal.append([event(n=1)])
    await journal.append([event(n=2)])
    await asyncio.wait_for(consumer, timeout=2)
    assert seen == [0, 1, 2]


def test_ids_and_timestamps_never_go_backwards_when_the_clock_does() -> None:
    gen = UlidGenerator(clock_ms=lambda: 1_700_000_000_000)
    ids = [gen.new() for _ in range(100)]
    assert ids == sorted(set(ids))
    times = iter([100, 100, 90, 150])
    clock = HybridClock("a", clock_ms=lambda: next(times))
    stamps = [clock.now() for _ in range(4)]
    assert stamps == sorted(stamps) and len(set(stamps)) == 4
    assert [s.encode() for s in stamps] == sorted(s.encode() for s in stamps)


def test_derived_trust_is_the_minimum_of_inputs() -> None:
    assert derive_trust([Trust.OWNER, Trust.WEB, Trust.SYSTEM]) == Trust.WEB
    assert derive_trust([]) == Trust.UNKNOWN
