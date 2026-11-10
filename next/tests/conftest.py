"""Shared fixtures. Every projection built on a test's `journal` is rebuilt from the journal
alone at the end of the test and must come back identical (D81): the whole suite doubles as a
replay test of every part of Telos. A test that breaks this on purpose carries
`@pytest.mark.no_rebuild_check`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest

from telos.core.events import NewEvent, Provenance, Trust
from telos.core.hlc import HybridClock
from telos.core.journal import SqliteJournal
from telos.core.projections import ProjectionRunner


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "no_rebuild_check: skip the end-of-test projection rebuild check (D81)"
    )


def make_event(kind: str = "test.happened", source: str = "test:1", **payload: Any) -> NewEvent:
    return NewEvent(
        kind=kind,
        payload=payload,
        provenance=Provenance(source=source, actor="owner:main"),
        trust=Trust.OWNER,
    )


@pytest.fixture
async def journal(tmp_path: Path, request: pytest.FixtureRequest) -> AsyncIterator[SqliteJournal]:
    async with SqliteJournal(tmp_path / "journal.sqlite3", HybridClock("test")) as j:
        yield j
        if request.node.get_closest_marker("no_rebuild_check") is None:
            # A projection the test already closed has no state left to compare.
            different: list[str] = []
            for runner in ProjectionRunner.on(j):
                if not any(getattr(p, "closed", False) for p in runner.projections):
                    different += await runner.verify()
            if different:
                pytest.fail(f"projections not rebuilt identically from the journal: {different}")
