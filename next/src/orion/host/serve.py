"""`orion serve`: the always-on process.

It opens the journal, journals `host.started`, runs the supervised services until SIGTERM or
SIGINT, then journals `host.stopped` with the reason. If a service keeps crashing, the
supervisor stops everything (`host.stopped`, reason `failure`) rather than running half-dead.
Signals are handled here, once for the whole process: services leave them alone.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from collections.abc import Mapping
from pathlib import Path

from orion import __version__
from orion.core.events import NewEvent, Provenance, Trust
from orion.core.hlc import HybridClock
from orion.core.journal import SqliteJournal
from orion.core.supervisor import RestartPolicy, ServiceFn, ServiceGaveUpError, Supervisor

log = logging.getLogger(__name__)

JOURNAL_FILE = "journal.sqlite3"
STARTED_KIND = "host.started"
STOPPED_KIND = "host.stopped"


def open_journal(data_dir: Path) -> SqliteJournal:
    return SqliteJournal(data_dir / JOURNAL_FILE, HybridClock("host"))


async def serve(
    data_dir: Path,
    services: Mapping[str, ServiceFn] | None = None,
    policy: RestartPolicy | None = None,
) -> int:
    """Run until signalled (exit code 0) or until a service gives up (exit code 1)."""
    await asyncio.to_thread(data_dir.mkdir, mode=0o700, parents=True, exist_ok=True)
    async with open_journal(data_dir) as journal:
        await journal.append([_lifecycle(STARTED_KIND, version=__version__, pid=os.getpid())])
        supervisor = Supervisor(journal)
        for name, fn in (services or {}).items():
            supervisor.add(name, fn, policy)
        running = asyncio.create_task(supervisor.run(), name="supervisor")
        signalled: list[str] = []

        def stop(sig: signal.Signals) -> None:
            signalled.append(sig.name)
            running.cancel()

        loop = asyncio.get_running_loop()
        if sys.platform != "win32":  # no loop signal handlers there; Ctrl+C still stops it
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, stop, sig)
        log.info("orion %s serving from %s", __version__, data_dir)
        try:
            await running
        except asyncio.CancelledError:
            if not signalled:
                raise
            log.info("orion stopped by %s", signalled[0])
            await journal.append([_lifecycle(STOPPED_KIND, reason=signalled[0])])
            return 0
        except ExceptionGroup as group:
            matched, rest = group.split(ServiceGaveUpError)
            if matched is None or rest is not None:
                raise
            gave_up = [str(e) for e in matched.exceptions]
            log.exception("orion stopping: %s", "; ".join(gave_up))
            await journal.append([_lifecycle(STOPPED_KIND, reason="failure", errors=gave_up)])
            return 1
        finally:
            if sys.platform != "win32":
                for sig in (signal.SIGTERM, signal.SIGINT):
                    loop.remove_signal_handler(sig)
        raise AssertionError("the supervisor only ends by cancellation or failure")


def _lifecycle(kind: str, **payload: object) -> NewEvent:
    return NewEvent(
        kind=kind,
        payload=payload,
        provenance=Provenance(source="host:serve", actor="system:host"),
        trust=Trust.SYSTEM,
    )
