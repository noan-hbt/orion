from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from orion.core.events import Trust
from orion.core.journal import SqliteJournal
from orion.memory.model import Category
from orion.memory.people import canonical, find, people_index, people_tools
from orion.memory.service import MemoryService, Origin
from orion.memory.store import MemoryStore, name_key
from orion.tools.base import Tool, ToolContext

OWNER = Origin(actor="orion:core", source="terminal:owner", trust=Trust.OWNER)
CTX = ToolContext(thread_id="owner", correlation_id="c")


@pytest.fixture
async def memory(journal: SqliteJournal) -> AsyncIterator[MemoryService]:
    store = MemoryStore(":memory:")
    await store.open()
    service = MemoryService(journal, store)
    await service.remember("Tom est allergique aux noix.", OWNER, about=["Tom"])
    await service.remember("Tom Lambert et Inès sont mariés.", OWNER, about=["Tom Lambert", "Inès"])
    await service.remember("Inès travaille chez Airbus.", OWNER, about=["Inès"])
    await service.remember("Alex aime le café serré.", OWNER, about=["Alex"],
                           category=Category.PREFERENCE)  # fmt: skip
    await service.add_commitment(
        "rendre le livre", OWNER, debtor="owner", creditor="Tom Lambert", due="2026-10-25"
    )
    yield service
    await store.close()


def tool(tools: list[Tool], name: str) -> Tool:
    return next(t for t in tools if t.name == name)


def test_names_compare_without_case_or_accents() -> None:
    assert name_key("  Inès ") == name_key("ines") == "ines"
    assert canonical("Paulo", {"paulo": "Tom", "tom": "Tom Lambert"}) == "Tom Lambert"
    assert canonical("a", {"a": "b", "b": "a"}) in {"a", "b"}  # a loop does not hang


async def test_aliases_merge_people_and_links_are_counted(memory: MemoryService) -> None:
    facts = await memory.store.facts()
    commitments = await memory.store.commitments(status=None)
    apart = people_index(facts, commitments, {}, {"Alex"})
    assert set(apart) == {"tom", "tom lambert", "ines"}  # the owner is not one of their people

    await memory.alias_person("Tom", "Tom Lambert", "même personne", OWNER)
    aliases = await memory.store.aliases()
    people = people_index(facts, commitments, aliases, {"Alex"})
    tom = people["tom lambert"]
    assert tom.aliases == {"Tom"} and len(tom.facts) == 2 and len(tom.commitments) == 1
    assert tom.related["Inès"] == 1 and people["ines"].related["Tom Lambert"] == 1
    assert find(people, "tom", aliases) == [tom]
    assert find(people, "Lambert", aliases) == [tom]  # a partial name
    assert find(people, "Jean", aliases) == []


async def test_person_tools(memory: MemoryService) -> None:
    tools = people_tools(memory, ["Alex"])
    person = tool(tools, "person")
    same = tool(tools, "same_person")
    exact = (await person.handler(person.parse('{"name": "Tom"}'), CTX)).content
    assert exact.startswith("Tom\n") and exact.endswith(
        "Noms proches : Tom Lambert (si c'est la même personne, dis-le avec people, action same)"
    )
    await memory.remember("Tom Durand est plombier.", OWNER, about=["Tom Durand"])
    ambiguous = await person.handler(person.parse('{"name": "Durand Tom"}'), CTX)
    assert ambiguous.content.startswith("Tom Durand\n")  # word order does not matter
    ambiguous = await person.handler(person.parse('{"name": "Lambert"}'), CTX)
    assert ambiguous.content.startswith("Tom Lambert\n")

    await same.handler(same.parse('{"name": "Tom", "same_as": "Tom Lambert"}'), CTX)
    profile = (await person.handler(person.parse('{"name": "tom"}'), CTX)).content.splitlines()
    assert profile[0] == "Tom Lambert (aussi : Tom)"
    assert any("allergique aux noix" in line for line in profile)
    assert any("rendre le livre" in line for line in profile)
    assert profile[-1] == "Lié à : Inès (1)"

    people = tool(tools, "people")
    listing = (await people.handler(people.parse("{}"), CTX)).content
    assert listing.splitlines()[0] == "- Tom Lambert: 2 fait(s), 1 engagement(s)"
    assert "Alex" not in listing
    assert same.effect.value == "internal" and not same.accepts_untrusted_context


async def test_forgetting_a_source_keeps_aliases_consistent(memory: MemoryService) -> None:
    await memory.alias_person(
        "Paulo", "Tom Lambert", "surnom", Origin(actor="x", source="mail:perso", trust=Trust.SYSTEM)
    )
    report = await memory.forget_source("mail:perso", "test", actor="owner:main")
    assert report.verified
    assert "paulo" not in await memory.store.aliases()
