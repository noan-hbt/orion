"""Event model shared by the whole system.

Every fact Orion holds is either an event in the journal or a projection derived from events.
Each event carries its provenance and a trust level; anything derived from several pieces of
content is never more trusted than its least trusted input.

One journal serves the whole instance, so an event says which agent and which thread it
concerns (`agent_id`, `thread_id`): scopes and per-agent views (R6.2) read them from the event
itself, not from each payload.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import IntEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from orion.core.ids import new_id

KIND_PATTERN = r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$"
"""A kind is dotted lowercase, at least two parts: `message.received`, `agent.created`."""


class Trust(IntEnum):
    """How much Orion may rely on a piece of content. Higher is more trusted."""

    UNKNOWN = 0
    WEB = 10
    THIRD_PARTY = 20
    SYSTEM = 50
    OWNER = 60


def derive_trust(inputs: Iterable[Trust]) -> Trust:
    """Trust of derived content: the minimum of its inputs. No inputs means UNKNOWN."""
    return min(inputs, default=Trust.UNKNOWN)


class Provenance(BaseModel):
    """Where a piece of content came from, who produced it, and what it was derived from."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(
        min_length=1, description="Origin, as 'kind:id', e.g. 'telegram:msg_123' or 'web:https://…'"
    )
    actor: str = Field(
        min_length=1, description="Who produced it, as 'kind:id', e.g. 'owner:main', 'system:host'"
    )
    agent: str | None = Field(
        default=None, description="Id of the agent that wrote it, if an agent did"
    )
    derived_from: tuple[str, ...] = Field(
        default=(), description="Ids of the events it derives from"
    )


class NewEvent(BaseModel):
    """An event before it is appended. The journal assigns sequence, timestamp and version."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=new_id)
    kind: str = Field(pattern=KIND_PATTERN, description="Dotted event type")
    payload: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance
    trust: Trust
    agent_id: str | None = Field(default=None, description="Agent this event concerns")
    thread_id: str | None = Field(default=None, description="Thread this event belongs to")
    causation_id: str | None = Field(
        default=None, description="Event that directly caused this one"
    )
    correlation_id: str | None = Field(default=None, description="Shared by all events of one flow")


class Event(NewEvent):
    """An event as stored in the journal, in today's shape."""

    seq: int = Field(description="Journal position, strictly increasing, gap-free")
    hlc: str = Field(description="Encoded hybrid logical clock timestamp")
    redacted: bool = False
