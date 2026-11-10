"""`telos serve` (R1.4): starts, journals its lifecycle, stops cleanly on SIGTERM."""

from __future__ import annotations

import asyncio
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from telos.core.events import Event
from telos.core.supervisor import RestartPolicy
from telos.host.serve import STARTED_KIND, STOPPED_KIND, open_journal, serve


@pytest.mark.skipif(sys.platform == "win32", reason="no SIGTERM to send on Windows")
def test_serve_starts_and_stops_on_sigterm(tmp_path: Path) -> None:
    process = subprocess.Popen(
        ["telos", "serve", "--data-dir", str(tmp_path / "data")],
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stderr is not None
    for line in process.stderr:  # pytest-timeout ends a serve that never says it is up
        if "serving" in line:
            break
    process.send_signal(signal.SIGTERM)
    process.stderr.read()
    process.stderr.close()
    assert process.wait(timeout=20) == 0
    events = asyncio.run(read_all(tmp_path / "data"))
    assert [e.kind for e in events] == [STARTED_KIND, STOPPED_KIND]
    assert events[-1].payload["reason"] == "SIGTERM"


async def read_all(data_dir: Path) -> list[Event]:
    async with open_journal(data_dir) as journal:
        return await journal.read()


async def test_serve_stops_in_failure_when_a_service_keeps_crashing(tmp_path: Path) -> None:
    async def broken() -> None:
        raise RuntimeError("always")

    fast = RestartPolicy(max_restarts=2, backoff_initial=0, backoff_max=0)
    assert await serve(tmp_path, {"broken": broken}, fast) == 1
    last = (await read_all(tmp_path))[-1]
    assert (last.kind, last.payload["reason"]) == (STOPPED_KIND, "failure")
