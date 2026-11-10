"""His address book (D159): the `.vcf` his phone exports, kept as an address book; its
birthdays watched by the relations module."""

from __future__ import annotations

from pathlib import Path

import pytest

from orion.config import OrionConfig
from orion.contacts.module import Contacts, contacts_tools
from orion.contacts.vcard import Birthday, parse
from orion.core.journal import SqliteJournal
from orion.core.projections import ProjectionRunner
from orion.mobile.upkeep import Upkeep, UpkeepError
from orion.relations.module import RelationState
from orion.tools.base import ToolContext

EXPORT = """BEGIN:VCARD
VERSION:3.0
UID:tom-1
FN:Tom Lambert
N:Lambert;Tom;;;
NICKNAME:Paulo
TEL;type=CELL:+33 6 12 34 56 78
item1.EMAIL;type=INTERNET:Tom.Lambert@example.com
BDAY:1994-03-12
ORG:Capgemini;
END:VCARD
BEGIN:VCARD
VERSION:3.0
FN:Maman
TEL:06 98 76 54 32
BDAY;X-APPLE-OMIT-YEAR=1604:1604-07-02
NOTE:une longue note qui
 continue ici
END:VCARD
BEGIN:VCARD
VERSION:2.1
N;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:In=C3=A8s;;;;
TEL;CELL:0611223344
END:VCARD
BEGIN:VCARD
VERSION:4.0
FN:Alex
BDAY:--0501
END:VCARD
BEGIN:VCARD
VERSION:3.0
TEL:0600000000
END:VCARD
"""


def test_a_phone_export_is_read() -> None:
    tom, mum, ines, owner = parse(EXPORT)  # a card without a name is skipped
    assert (tom.name, tom.nicknames, tom.org) == ("Tom Lambert", ("Paulo",), "Capgemini")
    assert tom.phones == ("+33612345678",) and tom.emails == ("tom.lambert@example.com",)
    assert tom.birthday == Birthday(3, 12, 1994)
    assert mum.birthday == Birthday(7, 2, None)  # iOS writes 1604 when the year is unknown
    assert ines.name == "Inès" and ines.phones == ("0611223344",) and ines.uid.startswith("h_")
    assert owner.birthday == Birthday(5, 1, None)
    assert "tél. +33612345678" in tom.line() and "12/03/1994" in tom.line()


async def test_his_address_book_is_kept_and_its_birthdays_watched(
    journal: SqliteJournal,
) -> None:
    contacts = Contacts(journal, ["Alex"])
    first = await contacts.import_vcards(EXPORT, "app")
    assert (first.added, first.changed, first.birthdays) == (4, 0, 2)  # not his own
    again = await contacts.import_vcards(EXPORT.replace("Capgemini", "Thales"), "app")
    assert (again.added, again.changed, again.unchanged, again.birthdays) == (0, 1, 3, 0)

    relations = RelationState()
    await ProjectionRunner(journal, [relations]).catch_up()
    assert {person for *_, person in relations.birthdays.values()} == {"Tom Lambert", "Maman"}

    (find,) = contacts_tools(contacts)
    ctx = ToolContext("owner", "c1")
    found = await find.handler(find.input_model(who="paulo"), ctx)
    assert "Thales" in found.content and "+33612345678" in found.content
    by_number = await find.handler(find.input_model(who="06 98 76 54 32"), ctx)
    assert "Maman" in by_number.content
    none = await find.handler(find.input_model(who="Gérard"), ctx)
    assert "Personne" in none.content


async def test_before_any_import_it_says_how(journal: SqliteJournal) -> None:
    (find,) = contacts_tools(Contacts(journal, []))
    said = await find.handler(find.input_model(who="Tom"), ToolContext("owner", "c1"))
    assert ".vcf" in said.content


async def test_his_address_book_from_the_app(journal: SqliteJournal, tmp_path: Path) -> None:
    contacts = Contacts(journal, [])
    upkeep = Upkeep(
        journal,
        OrionConfig.model_validate({"data_dir": tmp_path}),
        "https://orion.example",
        contacts=lambda: contacts,
    )
    assert (await upkeep.contacts_import(EXPORT))["added"] == 4
    with pytest.raises(UpkeepError):
        await upkeep.contacts_import("pas un export")
