"""Rows holding the values a start schema accepts but the runtime rarely writes.

Each rule names, per column, the values it puts there. Every table gets rows carrying the
rule's values in all the columns it targets at once; a row the schema rejects is retried
with one targeted column at a time, and what is still rejected goes to ``Seeder.notes``.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import asyncpg
from seeding import JSON_NULL, Column, Seeder

GHOST_ID = uuid.UUID("00000000-0000-4000-8000-00000000beef")
JSON_TYPES = {"json", "jsonb"}
TEXT_TYPES = {"varchar", "text", "bpchar", "citext"}
INT_TYPES = {"int2", "int4", "int8"}
# Text columns without a foreign key that name another row.
REFERENCE_NAMES = {
    "access_key",
    "creator",
    "domain",
    "endpoint",
    "group",
    "owner",
    "project",
    "registry",
    "resource_group",
    "scaling_group",
    "session",
    "user",
}

type Values = Callable[[Seeder, str, Column], list[Any]]

# Text columns the runtime writes only uuids into, with where it does. Rows hold a uuid
# string there; a migration may cast them.
UUID_TEXT: dict[tuple[str, str], str] = {
    ("audit_logs", "triggered_by"): "str(user.user_id) or NULL, actions/monitors since 25.15",
}

# Rows a migration refuses on purpose, left to the operator; the named scenario covers each.
# A copied row gets a new value in these columns.
RENEWED_ON_COPY: dict[tuple[str, str], str] = {
    ("vfolders", "name"): "b4c2e7f19a30, same_named_personal_folders",
}
# A custom role's permission rows naming another scope than the role's, which
# c092d242a027 refuses on purpose (custom_role_on_two_projects), are dropped: those not
# in the role's scope, or before roles had one, not in the scope of the role's first row.
_DROP_OFF_ROLE_SCOPE = """
    DELETE FROM permissions p USING roles r
    WHERE r.id = p.role_id AND r.source = 'custom'
      AND (p.scope_type, p.scope_id) IS DISTINCT FROM (r.scope_type, CAST(r.scope_id AS text))
"""
_DROP_OFF_FIRST_ROW_SCOPE = """
    DELETE FROM permissions p
    USING roles r,
          (SELECT DISTINCT ON (role_id) role_id, scope_type, scope_id
           FROM permissions ORDER BY role_id, id) f
    WHERE r.id = p.role_id AND r.source = 'custom' AND f.role_id = p.role_id
      AND (p.scope_type, p.scope_id) IS DISTINCT FROM (f.scope_type, f.scope_id)
"""
# A route is made with its deployment's owner, and a purge delegating ownership moves both.
_ROUTE_OWNER_IS_DEPLOYMENT_OWNER = """
    UPDATE endpoints e SET session_owner = r.session_owner
    FROM routings r WHERE r.endpoint = e.id
"""
# The runtime writes the bit of the row's operation (c6648c039bd4).
_BIT_OF_OPERATION = """
    UPDATE permissions SET permission = CASE operation
        WHEN 'read' THEN 1 WHEN 'update' THEN 2 WHEN 'create' THEN 4
        WHEN 'soft-delete' THEN 8 WHEN 'hard-delete' THEN 16 ELSE 0 END
"""


@dataclass(frozen=True)
class ValueRule:
    name: str
    description: str
    values: Values


def _nulls(_s: Seeder, _table: str, column: Column) -> list[Any]:
    return [None] if column.nullable else []


def _json_null(_s: Seeder, _table: str, column: Column) -> list[Any]:
    return [JSON_NULL] if column.udt_name in JSON_TYPES else []


def _empty(s: Seeder, table: str, column: Column) -> list[Any]:
    if (
        s.foreign_key(table, column.name)
        or s.allowed_values(table, column)
        or (table, column.name) in UUID_TEXT
    ):
        return []
    if column.udt_name in TEXT_TYPES:
        return [""]
    if column.udt_name in JSON_TYPES:
        return [{}, []]
    if column.udt_name.startswith("_"):
        return [[]]
    return []


def _is_reference(name: str) -> bool:
    return name in REFERENCE_NAMES or name.endswith(("_id", "_uuid", "_name"))


def _dangling(s: Seeder, table: str, column: Column) -> list[Any]:
    if s.foreign_key(table, column.name) or s.is_unique(table, column.name):
        return []
    if column.udt_name == "uuid":
        return [GHOST_ID]
    if (table, column.name) in UUID_TEXT:
        return [str(GHOST_ID)]
    if column.udt_name in TEXT_TYPES and _is_reference(column.name):
        if s.allowed_values(table, column):
            return []
        return [str(GHOST_ID) if column.name.endswith(("_id", "_uuid")) else "ghost"]
    return []


def _every_allowed(s: Seeder, table: str, column: Column) -> list[Any]:
    return list(s.allowed_values(table, column))


RULES: dict[str, ValueRule] = {
    r.name: r
    for r in [
        ValueRule("nulls", "NULL in every nullable column", _nulls),
        ValueRule("json_null", "JSON null in every json column", _json_null),
        ValueRule(
            "empty_values",
            "'' in free text, {} and [] in json, '{}' in arrays",
            _empty,
        ),
        ValueRule(
            "dangling_refs",
            "an id no row holds in every uuid or reference-named column without a foreign key",
            _dangling,
        ),
        ValueRule("every_enum_value", "every value of every enum column", _every_allowed),
    ]
}


async def _try_insert(s: Seeder, table: str, row: dict[str, Any]) -> str | None:
    """Insert the row; return why the schema rejected it, if it did."""
    error: str | None = None
    # A unique column filled from a random parent may collide; try again.
    for _ in range(3):
        try:
            async with s.conn.transaction():
                await s.insert(table, **row)
            return None
        except asyncpg.UniqueViolationError as e:
            error = f"{type(e).__name__}: {e}"
        except (asyncpg.PostgresError, ValueError, TypeError) as e:
            return f"{type(e).__name__}: {e}"
    return error


async def _base_row(s: Seeder, table: str, skip: set[str]) -> dict[str, Any]:
    """Values for the columns a rule does not target, nullable ones included.

    A nullable foreign key whose parent table is empty stays NULL.
    """
    row = await s.fill_composite_keys(table, skip)
    for column in s.columns(table):
        if column.name in skip or column.name in row or column.has_default:
            continue
        if (table, column.name) in UUID_TEXT:
            row[column.name] = str(uuid.uuid4())
            continue
        try:
            row[column.name] = await s.fill(table, column)
        except LookupError:
            if not column.nullable:
                raise
    return row


def _fit(column: Column, value: Any) -> Any:
    if isinstance(value, str) and column.max_length is not None:
        return value[: column.max_length]
    return value


async def _in_passes(s: Seeder, seed_table: Callable[[str], Awaitable[None]]) -> None:
    """Seed every table; a table whose parent table is still empty waits for a later pass."""
    pending = s.tables()
    while pending:
        waiting = []
        for table in pending:
            try:
                await seed_table(table)
            except LookupError as e:
                waiting.append((table, str(e)))
        if len(waiting) == len(pending):
            s.notes += [f"{table}: {reason}" for table, reason in waiting]
            return
        pending = [table for table, _ in waiting]


async def seed_rule(s: Seeder, rule: ValueRule) -> None:
    async def seed_table(table: str) -> None:
        await _seed_table(s, rule, table)

    await _in_passes(s, seed_table)
    await _align(s)


async def _seed_table(s: Seeder, rule: ValueRule, table: str) -> None:
    columns = {c.name: c for c in s.columns(table) if not c.generated}
    targeted = {
        name: [_fit(column, v) for v in values]
        for name, column in columns.items()
        if (values := rule.values(s, table, column))
    }
    if not targeted:
        # A child table of a rule-targeted table needs a parent row.
        await _ensure_row(s, table)
        return
    for i in range(max(len(v) for v in targeted.values())):
        # A value already tried is not repeated, which a unique column would reject.
        current = {name: values[i] for name, values in targeted.items() if i < len(values)}
        base = await _base_row(s, table, set(current))
        if await _try_insert(s, table, base | current) is None:
            continue
        for name, value in current.items():
            single = await _base_row(s, table, {name})
            error = await _try_insert(s, table, single | {name: value})
            if error is not None:
                s.notes.append(f"{table}.{name}: rejected: {error.splitlines()[0][:200]}")


async def _ensure_row(s: Seeder, table: str) -> None:
    if await s.conn.fetchval(f'SELECT NOT EXISTS (SELECT FROM "{table}")'):
        error = await _try_insert(s, table, await _base_row(s, table, set()))
        if error is not None:
            s.notes.append(f"{table}: rejected: {error.splitlines()[0][:200]}")


async def seed_duplicates(s: Seeder) -> None:
    """Give every empty table a row, then copy one row of every table, renewing only the
    columns a unique index covers."""

    async def seed_table(table: str) -> None:
        await _ensure_row(s, table)

    await _in_passes(s, seed_table)
    await _align(s)
    for table in s.tables():
        columns = [
            c
            for c in s.columns(table)
            if not c.generated and not (c.has_default and s.is_unique(table, c.name))
        ]
        exprs = [_renewed(s, table, c) for c in columns]
        names = ", ".join(f'"{c.name}"' for c in columns)
        try:
            async with s.conn.transaction():
                await s.conn.execute(
                    f'INSERT INTO "{table}" ({names}) SELECT {", ".join(exprs)} FROM "{table}" t'
                    f' WHERE t.ctid = (SELECT ctid FROM "{table}" LIMIT 1)'
                )
        except asyncpg.PostgresError as e:
            s.notes.append(f"{table}: rejected: {type(e).__name__}: {str(e).splitlines()[0][:200]}")


async def _align(s: Seeder) -> None:
    if s.has_column("routings", "session_owner"):
        await s.conn.execute(_ROUTE_OWNER_IS_DEPLOYMENT_OWNER)
    if not s.has_column("permissions", "scope_type"):
        return
    if s.has_column("roles", "scope_type"):
        await s.conn.execute(_DROP_OFF_ROLE_SCOPE)
    else:
        await s.conn.execute(_DROP_OFF_FIRST_ROW_SCOPE)
    if s.has_column("permissions", "operation") and s.has_column("permissions", "permission"):
        await s.conn.execute(_BIT_OF_OPERATION)


def _renewed(s: Seeder, table: str, column: Column) -> str:
    ref = f't."{column.name}"'
    renewed = (table, column.name) in RENEWED_ON_COPY
    if not renewed and (not s.is_unique(table, column.name) or s.foreign_key(table, column.name)):
        return ref
    if column.udt_name == "uuid":
        return "uuid_generate_v4()"
    if column.udt_name in TEXT_TYPES:
        return f"left(md5(random()::text), {column.max_length or 32})"
    if column.udt_name in INT_TYPES:
        return f'(SELECT max("{column.name}") + 1 FROM "{table}")'
    return ref
