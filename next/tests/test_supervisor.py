"""Supervision (R1.4): a crashing service is restarted and journaled; one that keeps crashing
stops the whole tree after warning."""

from __future__ import annotations

import asyncio

import pytest

from orion.core.journal import SqliteJournal
from orion.core.supervisor import (
    CRASHED_KIND,
    GAVE_UP_KIND,
    RestartPolicy,
    ServiceGaveUpError,
    Supervisor,
)

FAST = RestartPolicy(max_restarts=3, window_seconds=60, backoff_initial=0, backoff_max=0)


async def kinds(journal: SqliteJournal) -> list[tuple[str, object]]:
    return [(e.kind, e.payload.get("service")) for e in await journal.read()]


async def test_crashing_service_is_restarted_and_journaled(journal: SqliteJournal) -> None:
    attempts = 0
    recovered = asyncio.Event()

    async def flaky() -> None:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("transient")
        recovered.set()
        await asyncio.Event().wait()

    supervisor = Supervisor(journal)
    supervisor.add("flaky", flaky, FAST)
    task = asyncio.create_task(supervisor.run())
    await asyncio.wait_for(recovered.wait(), timeout=5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert await kinds(journal) == [(CRASHED_KIND, "flaky")] * 2
    assert "transient" in (await journal.read())[0].payload["error"]


async def test_service_past_its_budget_escalates_and_stops_the_tree(
    journal: SqliteJournal,
) -> None:
    escalations: list[str] = []
    sibling_cancelled = asyncio.Event()

    async def broken() -> None:
        raise RuntimeError("always")

    async def healthy() -> None:
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            sibling_cancelled.set()
            raise

    async def escalate(service: str, error: BaseException) -> None:
        escalations.append(service)

    supervisor = Supervisor(journal, escalate=escalate)
    supervisor.add("broken", broken, FAST)
    supervisor.add("healthy", healthy, FAST)
    with pytest.raises(ExceptionGroup) as info:
        await asyncio.wait_for(supervisor.run(), timeout=5)
    assert info.group_contains(ServiceGaveUpError)
    assert escalations == ["broken"]
    assert sibling_cancelled.is_set()
    assert (await kinds(journal))[-1] == (GAVE_UP_KIND, "broken")
