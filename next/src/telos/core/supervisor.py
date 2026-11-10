"""Supervision of long-running services, Erlang-style.

A service that crashes is logged, journaled (`service.crashed`) and restarted with backoff. If
it keeps crashing past its restart budget, the supervisor journals `service.gave_up`, calls the
escalation hook (to warn the owner) and stops the whole tree, rather than limping along with a
dead component. Nothing dies silently.

A service is meant to run forever: one that returns counts as a crash. A server inside a
service must leave signals to the process (`telos.host.serve` handles them once for all):
otherwise a server that returns on SIGTERM looks like a crash and restarts in a loop.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from telos.core.events import Event, NewEvent, Provenance, Trust

log = logging.getLogger(__name__)

ServiceFn = Callable[[], Awaitable[None]]
EscalationHook = Callable[[str, BaseException], Awaitable[None]]

CRASHED_KIND = "service.crashed"
GAVE_UP_KIND = "service.gave_up"


class Appender(Protocol):
    """What the supervisor needs from the journal."""

    async def append(self, events: Sequence[NewEvent]) -> list[Event]: ...


class ServiceGaveUpError(RuntimeError):
    """Raised when a service exhausts its restart budget."""

    def __init__(self, service: str, last_error: BaseException) -> None:
        super().__init__(f"service {service!r} exceeded its restart budget")
        self.service = service
        self.last_error = last_error


@dataclass(frozen=True)
class RestartPolicy:
    max_restarts: int = 5
    """Crashes allowed within `window_seconds`; one more and the service gives up."""
    window_seconds: float = 60.0
    backoff_initial: float = 0.5
    backoff_max: float = 30.0


@dataclass
class _ServiceSpec:
    name: str
    fn: ServiceFn
    policy: RestartPolicy
    crashes: deque[float] = field(default_factory=deque[float])


async def _no_escalation(_service: str, _error: BaseException) -> None:
    return None


class Supervisor:
    def __init__(
        self,
        journal: Appender,
        escalate: EscalationHook = _no_escalation,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._journal = journal
        self._services: list[_ServiceSpec] = []
        self._escalate = escalate
        self._monotonic = monotonic

    def add(self, name: str, fn: ServiceFn, policy: RestartPolicy | None = None) -> None:
        if any(s.name == name for s in self._services):
            raise ValueError(f"service {name!r} already registered")
        self._services.append(_ServiceSpec(name, fn, policy or RestartPolicy()))

    @property
    def services(self) -> list[str]:
        return [spec.name for spec in self._services]

    async def run(self) -> None:
        """Run every service until cancelled, or until one gives up (then raise
        `ServiceGaveUpError`, inside an `ExceptionGroup`). With no service, wait until
        cancelled."""
        async with asyncio.TaskGroup() as group:
            for spec in self._services:
                group.create_task(self._supervise(spec), name=f"supervise:{spec.name}")
            if not self._services:
                await asyncio.Event().wait()

    async def _supervise(self, spec: _ServiceSpec) -> None:
        backoff = spec.policy.backoff_initial
        while True:
            try:
                log.info("service %s: start", spec.name)
                await spec.fn()
                log.warning("service %s: returned unexpectedly", spec.name)
                error: BaseException = RuntimeError("service returned unexpectedly")
            except asyncio.CancelledError:
                log.info("service %s: cancelled", spec.name)
                raise
            except Exception as exc:
                log.exception("service %s: crashed", spec.name)
                error = exc

            now = self._monotonic()
            spec.crashes.append(now)
            while spec.crashes and now - spec.crashes[0] > spec.policy.window_seconds:
                spec.crashes.popleft()
            gave_up = len(spec.crashes) > spec.policy.max_restarts
            # A journal that cannot record the crash is not swallowed: it stops the tree.
            await self._record(CRASHED_KIND, spec, error)
            if gave_up:
                log.error("service %s: gave up after %d crashes", spec.name, len(spec.crashes))
                await self._record(GAVE_UP_KIND, spec, error)
                await self._escalate(spec.name, error)
                raise ServiceGaveUpError(spec.name, error) from error

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, spec.policy.backoff_max)

    async def _record(self, kind: str, spec: _ServiceSpec, error: BaseException) -> None:
        await self._journal.append(
            [
                NewEvent(
                    kind=kind,
                    payload={
                        "service": spec.name,
                        "error": repr(error)[:1000],
                        "recent_crashes": len(spec.crashes),
                    },
                    provenance=Provenance(source=f"service:{spec.name}", actor="system:host"),
                    trust=Trust.SYSTEM,
                )
            ]
        )
