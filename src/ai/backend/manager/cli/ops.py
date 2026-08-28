from __future__ import annotations

import asyncio
import dataclasses
import inspect
import json
import textwrap
from collections.abc import Sequence
from itertools import groupby
from typing import Any, Final

import click
from tabulate import tabulate

from ai.backend.manager.actions.registry.types import Concern, WiredProcessor
from ai.backend.manager.actions.types import (
    ActionBacking,
    ActionGate,
    ActionKind,
    ActionOperationType,
)
from ai.backend.manager.services.catalog import load_wiring_catalog

_COLUMNS: Final[tuple[str, ...]] = (
    "concern",
    "entity_type",
    "field_type",
    "operation",
    "action_name",
    "kind",
    "gate",
    "backing",
)
# The columns of an entity block, which its area heads.
_ENTITY_BLOCK_COLUMNS: Final[tuple[str, ...]] = (
    "entity_type",
    "operation",
    "action_name",
    "kind",
    "gate",
    "backing",
)
# The columns of a field block, whose header names the field type and its owner.
_FIELD_BLOCK_COLUMNS: Final[tuple[str, ...]] = tuple(
    column for column in _ENTITY_BLOCK_COLUMNS if column != "entity_type"
)
_ENTITY_COLUMNS: Final[tuple[str, ...]] = ("concern", "entity_type", "field_type", "operations")
# Stands for a column a wiring leaves unset, so every line has the same shape.
_ABSENT: Final[str] = "-"
# An operation targeting no entity at all, which only a relation does. Distinct from
# `global`, which names an operation over every entity.
_NO_ENTITY: Final[str] = "(none)"


@dataclasses.dataclass(frozen=True)
class CatalogEntry:
    """One wiring, as the catalog prints it."""

    concern: str
    entity_type: str
    field_type: str
    operation: str
    action_name: str
    kind: str
    gate: str
    backing: str
    action_cls: type[Any]

    @classmethod
    def from_wiring(cls, wiring: WiredProcessor) -> CatalogEntry:
        return cls(
            concern=str(wiring.concern),
            entity_type=str(wiring.entity_type) if wiring.entity_type is not None else _NO_ENTITY,
            field_type=str(wiring.field_type) if wiring.field_type is not None else _ABSENT,
            operation=str(wiring.action_cls.operation_type()),
            action_name=wiring.action_cls.action_name(),
            kind=str(wiring.kind),
            gate=str(wiring.gate),
            backing=str(wiring.backing),
            action_cls=wiring.action_cls,
        )

    def sort_key(self) -> tuple[str, ...]:
        return (
            self.concern,
            self.entity_type,
            self.field_type,
            self.operation,
            self.action_name,
        )

    def values(self, columns: Sequence[str]) -> tuple[str, ...]:
        return tuple(getattr(self, column) for column in columns)

    def to_dict(self) -> dict[str, str]:
        return {column: getattr(self, column) for column in _COLUMNS}

    def defined_at(self) -> str:
        source_file = inspect.getsourcefile(self.action_cls)
        _, line = inspect.getsourcelines(self.action_cls)
        return f"{source_file}:{line}"

    def input_fields(self) -> list[tuple[str, str]]:
        if not dataclasses.is_dataclass(self.action_cls):
            return []
        return [(f.name, _type_name(f.type)) for f in dataclasses.fields(self.action_cls)]


@dataclasses.dataclass(frozen=True)
class EntityFields:
    """One entity type of one area, and the field types under it.

    ``global`` holds the field types whose rows name their owner as a value, which
    leaves the wiring no entity type to fix.
    """

    concern: str
    entity_type: str
    operations: int
    fields: tuple[tuple[str, int], ...]

    def rows(self) -> list[tuple[str, ...]]:
        rows: list[tuple[str, ...]] = [
            (self.concern, self.entity_type, _ABSENT, str(self.operations))
        ]
        rows.extend(
            (self.concern, self.entity_type, field, str(count)) for field, count in self.fields
        )
        return rows


def _type_name(annotation: Any) -> str:
    return annotation.__name__ if isinstance(annotation, type) else str(annotation)


def _load_entries() -> list[CatalogEntry]:
    catalog = asyncio.run(load_wiring_catalog())
    return sorted(
        (CatalogEntry.from_wiring(wiring) for wiring in catalog),
        key=lambda entry: entry.sort_key(),
    )


def _load_entity_fields() -> list[EntityFields]:
    direct: dict[tuple[str, str], int] = {}
    owned: dict[tuple[str, str], dict[str, int]] = {}
    for entry in _load_entries():
        key = (entry.concern, entry.entity_type)
        direct.setdefault(key, 0)
        owned.setdefault(key, {})
        if entry.field_type == _ABSENT:
            direct[key] += 1
        else:
            fields = owned[key]
            fields[entry.field_type] = fields.get(entry.field_type, 0) + 1
    return [
        EntityFields(concern, entity_type, direct[key], tuple(sorted(owned[key].items())))
        for key in sorted(direct)
        for concern, entity_type in (key,)
    ]


def _print_block(rows: Sequence[tuple[str, ...]], columns: Sequence[str], indent: str) -> None:
    print(textwrap.indent(tabulate(rows, headers=columns, tablefmt="plain"), indent))


def _print_table(entries: Sequence[CatalogEntry]) -> None:
    """Print one block per area: the operations naming an entity, then a block per
    field type under the entity answering for its rows."""
    concerns = 0
    for concern, group in groupby(entries, key=lambda entry: entry.concern):
        block = list(group)
        concerns += 1
        print(f"{concern} ({len(block)})")
        on_entities = [entry for entry in block if entry.field_type == _ABSENT]
        if on_entities:
            _print_block(
                [entry.values(_ENTITY_BLOCK_COLUMNS) for entry in on_entities],
                _ENTITY_BLOCK_COLUMNS,
                "  ",
            )
        for field_type, field_group in groupby(
            (entry for entry in block if entry.field_type != _ABSENT),
            key=lambda entry: entry.field_type,
        ):
            on_field = list(field_group)
            owners = ", ".join(sorted({entry.entity_type for entry in on_field}))
            print(f"  {field_type} ({len(on_field)}) of {owners}")
            _print_block(
                [entry.values(_FIELD_BLOCK_COLUMNS) for entry in on_field],
                _FIELD_BLOCK_COLUMNS,
                "    ",
            )
        print()
    print(f"{len(entries)} operations in {concerns} concern{'' if concerns == 1 else 's'}")


def _print_entries(entries: Sequence[CatalogEntry], output: str) -> None:
    match output:
        case "json":
            print(json.dumps([entry.to_dict() for entry in entries], indent=2))
        case "tsv":
            print("\t".join(_COLUMNS))
            for entry in entries:
                print("\t".join(entry.values(_COLUMNS)))
        case _:
            if not entries:
                print("No wired operation matches the given filters.")
                return
            _print_table(entries)


def _column_legend() -> str:
    """The values of the declared columns and what each one means."""
    lines = ["Columns:", "", "\b"]
    for column, members in (
        ("kind", tuple(ActionKind)),
        ("gate", tuple(ActionGate)),
        ("backing", tuple(ActionBacking)),
    ):
        lines.append(f"  {column}")
        width = max(len(member.value) for member in members)
        for member in members:
            lines.append(f"    {member.value:<{width}}  {member.describe()}")
    return "\n".join(lines)


@click.group()
def cli() -> None:
    """Command set for inspecting the wired domain operation catalog."""


_LIST_HELP: Final[
    str
] = """List the wired domain operations, every one of them unless a filter is given.

Reads the catalog the processor assembly records, without starting any manager
dependency: no database, no leader election, no event consumer. A processor still on
the legacy base is wired outside the registry, so it is not recorded here.

{legend}

Examples:

\b
  $ backend.ai mgr ops list --concern vfolder
  $ backend.ai mgr ops list --gate anonymous
  $ backend.ai mgr ops list --output json
"""


@cli.command(name="list", help=_LIST_HELP.format(legend=_column_legend()))
@click.option(
    "--concern",
    default=None,
    type=click.Choice([concern.value for concern in Concern]),
    help="Keep only the operations of this area.",
)
@click.option("--entity", default=None, help="Keep only the operations on this entity type.")
@click.option("--field", default=None, help="Keep only the operations on this field type.")
@click.option(
    "--operation",
    default=None,
    type=click.Choice([operation.value for operation in ActionOperationType]),
    help="Keep only the operations performing this operation.",
)
@click.option(
    "--gate",
    default=None,
    type=click.Choice([gate.value for gate in ActionGate]),
    help="Keep only the operations behind this gate.",
)
@click.option(
    "--backing",
    default=None,
    type=click.Choice([backing.value for backing in ActionBacking]),
    help="Keep only the operations run by this backing.",
)
@click.option(
    "-o",
    "--output",
    default="table",
    type=click.Choice(["table", "json", "tsv"]),
    help="Set the output style of the command results.",
)
def list_operations(
    concern: str | None,
    entity: str | None,
    field: str | None,
    operation: str | None,
    gate: str | None,
    backing: str | None,
    output: str,
) -> None:
    entries = _load_entries()
    if concern is not None:
        entries = [entry for entry in entries if entry.concern == concern]
    if entity is not None:
        entries = [entry for entry in entries if entry.entity_type == entity]
    if field is not None:
        entries = [entry for entry in entries if entry.field_type == field]
    if operation is not None:
        entries = [entry for entry in entries if entry.operation == operation]
    if gate is not None:
        entries = [entry for entry in entries if entry.gate == gate]
    if backing is not None:
        entries = [entry for entry in entries if entry.backing == backing]
    _print_entries(entries, output)


@cli.command(name="entities")
@click.option(
    "-o",
    "--output",
    default="table",
    type=click.Choice(["table", "json", "tsv"]),
    help="Set the output style of the command results.",
)
def list_entities(output: str) -> None:
    """
    List what the wiring names, area first: the entity types of each area and the
    field types under each entity type.

    An entity type's own count is the operations naming it directly; a field type's is
    the operations over its rows. Field types under `global` name their owner as a
    value, so the wiring fixes no entity type for them.

    Examples:

        $ backend.ai mgr ops entities
    """
    entities = _load_entity_fields()
    match output:
        case "json":
            print(
                json.dumps(
                    [
                        dict(zip(_ENTITY_COLUMNS, row, strict=True))
                        for entity in entities
                        for row in entity.rows()
                    ],
                    indent=2,
                )
            )
        case "tsv":
            print("\t".join(_ENTITY_COLUMNS))
            for entity in entities:
                for row in entity.rows():
                    print("\t".join(row))
        case _:
            concerns = 0
            entity_types: set[str] = set()
            field_types: set[str] = set()
            width = max(len(entity.concern) for entity in entities) if entities else 0
            for concern, group in groupby(entities, key=lambda entity: entity.concern):
                concerns += 1
                print(f"{concern:<{width}}  {Concern(concern).describe()}")
                for entity in group:
                    entity_types.add(entity.entity_type)
                    print(f"  {entity.entity_type} ({entity.operations})")
                    for field, count in entity.fields:
                        field_types.add(field)
                        print(f"    {field} ({count})")
                print()
            print(
                f"{concerns} concerns, {len(entity_types)} entity types, "
                f"{len(field_types)} field types"
            )


@cli.command(name="describe")
@click.argument("entity_type")
@click.argument("action_name")
def describe_operation(entity_type: str, action_name: str) -> None:
    """
    Describe the operations wired as ENTITY_TYPE ACTION_NAME.

    The address is the (entity type, operation, action name) triple, so a pair that
    several wirings share prints all of them.

    Examples:

        $ backend.ai mgr ops describe vfolder create_vfolder
    """
    matched = [
        entry
        for entry in _load_entries()
        if entry.entity_type == entity_type and entry.action_name == action_name
    ]
    if not matched:
        raise click.ClickException(f"No operation is wired as {entity_type} {action_name}.")
    for entry in matched:
        print(
            tabulate(
                [
                    *((column, getattr(entry, column)) for column in _COLUMNS),
                    (
                        "action_class",
                        f"{entry.action_cls.__module__}.{entry.action_cls.__qualname__}",
                    ),
                    ("defined_at", entry.defined_at()),
                ],
                tablefmt="plain",
            )
        )
        fields = entry.input_fields()
        if fields:
            print("input_fields")
            print(textwrap.indent(tabulate(fields, tablefmt="plain"), "  "))
        print()
