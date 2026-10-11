"""Insert rows into whatever schema a start revision has, filling the columns a scenario leaves out.

A NOT NULL column without a default gets the first row of the table its foreign key
points at, or a placeholder of its type. Scenarios name only the columns they are about.
"""

from __future__ import annotations

import datetime
import json
import secrets
import uuid
from dataclasses import dataclass
from typing import Any

import asyncpg


class JsonNull:
    """The JSON ``null`` a JSON column holds, as opposed to SQL NULL."""


JSON_NULL = JsonNull()


def _dump_json(value: Any) -> str:
    return "null" if value is JSON_NULL else json.dumps(value)


@dataclass(frozen=True)
class Column:
    name: str
    udt_name: str
    nullable: bool
    has_default: bool
    generated: bool
    max_length: int | None


class Seeder:
    conn: asyncpg.Connection
    _columns: dict[str, list[Column]]
    _foreign_keys: dict[tuple[str, str], tuple[str, str]]
    _composite_keys: dict[str, list[tuple[list[str], str, list[str]]]]
    _enum_labels: dict[str, list[str]]
    _allowed: dict[tuple[str, str], list[str]]
    _unique: set[tuple[str, str]]
    notes: list[str]

    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn
        self._columns = {}
        self._foreign_keys = {}
        self._composite_keys = {}
        self._enum_labels = {}
        self._allowed = {}
        self._unique = set()
        self.notes = []

    @classmethod
    async def connect(cls, dsn: str) -> Seeder:
        conn = await asyncpg.connect(dsn)
        for codec in ("json", "jsonb"):
            await conn.set_type_codec(
                codec, encoder=_dump_json, decoder=json.loads, schema="pg_catalog"
            )
        seeder = cls(conn)
        await seeder.refresh()
        return seeder

    async def close(self) -> None:
        await self.conn.close()

    async def refresh(self) -> None:
        self._columns = {}
        for r in await self.conn.fetch(
            """
            SELECT table_name, column_name, udt_name, is_nullable = 'YES' AS nullable,
                   (column_default IS NOT NULL OR is_identity = 'YES'
                    OR is_generated = 'ALWAYS') AS has_default,
                   (is_generated = 'ALWAYS' OR identity_generation = 'ALWAYS') AS generated,
                   character_maximum_length AS max_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
        ):
            self._columns.setdefault(r["table_name"], []).append(
                Column(
                    r["column_name"],
                    r["udt_name"],
                    r["nullable"],
                    r["has_default"],
                    r["generated"],
                    r["max_length"],
                )
            )
        self._foreign_keys = {
            (r["src_table"], r["src_column"]): (r["dst_table"], r["dst_column"])
            for r in await self.conn.fetch(
                """
                SELECT src.relname AS src_table, sa.attname AS src_column,
                       dst.relname AS dst_table, da.attname AS dst_column
                FROM pg_constraint c
                JOIN pg_class src ON src.oid = c.conrelid
                JOIN pg_class dst ON dst.oid = c.confrelid
                JOIN pg_attribute sa ON sa.attrelid = c.conrelid AND sa.attnum = c.conkey[1]
                JOIN pg_attribute da ON da.attrelid = c.confrelid AND da.attnum = c.confkey[1]
                WHERE c.contype = 'f' AND array_length(c.conkey, 1) = 1
                """
            )
        }
        self._composite_keys = {}
        for r in await self.conn.fetch(
            """
            SELECT src.relname AS src_table, dst.relname AS dst_table,
                   ARRAY(SELECT attname FROM unnest(c.conkey) WITH ORDINALITY k(n, i)
                         JOIN pg_attribute ON attrelid = c.conrelid AND attnum = k.n
                         ORDER BY k.i) AS src_columns,
                   ARRAY(SELECT attname FROM unnest(c.confkey) WITH ORDINALITY k(n, i)
                         JOIN pg_attribute ON attrelid = c.confrelid AND attnum = k.n
                         ORDER BY k.i) AS dst_columns
            FROM pg_constraint c
            JOIN pg_class src ON src.oid = c.conrelid
            JOIN pg_class dst ON dst.oid = c.confrelid
            WHERE c.contype = 'f' AND array_length(c.conkey, 1) > 1
            """
        ):
            self._composite_keys.setdefault(r["src_table"], []).append((
                list(r["src_columns"]),
                r["dst_table"],
                list(r["dst_columns"]),
            ))
        self._enum_labels = {}
        for r in await self.conn.fetch(
            """
            SELECT t.typname, e.enumlabel FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid
            ORDER BY t.typname, e.enumsortorder
            """
        ):
            self._enum_labels.setdefault(r["typname"], []).append(r["enumlabel"])
        self._unique = {
            (r["table_name"], r["column_name"])
            for r in await self.conn.fetch(
                """
                SELECT t.relname AS table_name, a.attname AS column_name
                FROM pg_index i
                JOIN pg_class t ON t.oid = i.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace AND n.nspname = 'public'
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
                WHERE i.indisunique
                """
            )
        }
        self._allowed = {}
        if await self.conn.fetchval("SELECT to_regclass('upgrade_check.column_values')"):
            self._allowed = {
                (r["table_name"], r["column_name"]): list(r["allowed"])
                for r in await self.conn.fetch("SELECT * FROM upgrade_check.column_values")
            }

    def has_table(self, table: str) -> bool:
        return table in self._columns

    def has_column(self, table: str, column: str) -> bool:
        return any(c.name == column for c in self._columns.get(table, []))

    def tables(self) -> list[str]:
        return sorted(t for t in self._columns if t != "alembic_version")

    def columns(self, table: str) -> list[Column]:
        return self._columns[table]

    def foreign_key(self, table: str, column: str) -> tuple[str, str] | None:
        return self._foreign_keys.get((table, column))

    async def fill_composite_keys(self, table: str, skip: set[str]) -> dict[str, Any]:
        """Columns of the table's multi-column foreign keys, taken from one parent row."""
        values: dict[str, Any] = {}
        for src_columns, dst_table, dst_columns in self._composite_keys.get(table, []):
            if skip & set(src_columns):
                continue
            selected = ", ".join(f'"{c}"' for c in dst_columns)
            parent = await self.conn.fetchrow(
                f'SELECT {selected} FROM "{dst_table}" ORDER BY random() LIMIT 1'
            )
            if parent is None:
                raise LookupError(f"{table} needs a row in {dst_table} first")
            values |= dict(zip(src_columns, parent.values(), strict=True))
        return values

    def is_unique(self, table: str, column: str) -> bool:
        """The column is part of a primary key or a unique index."""
        return (table, column) in self._unique

    def allowed_values(self, table: str, column: Column) -> list[str]:
        """The labels of the column's database enum or of the Python enum the release maps it to."""
        return self._enum_labels.get(column.udt_name) or self._allowed.get((table, column.name), [])

    def enum_labels(self, udt_name: str) -> list[str]:
        return self._enum_labels.get(udt_name, [])

    async def insert(self, table: str, **values: Any) -> asyncpg.Record:
        """Insert one row and return it; unknown keys are an error."""
        columns = {c.name: c for c in self._columns[table]}
        unknown = set(values) - set(columns)
        if unknown:
            raise KeyError(f"{table} has no column(s) {sorted(unknown)}")
        row = dict(values)
        for column in columns.values():
            if column.name in row or column.nullable or column.has_default:
                continue
            row[column.name] = await self.fill(table, column)
        names = list(row)
        placeholders = [
            f"${i + 1}::{_cast(columns[name].udt_name)}" for i, name in enumerate(names)
        ]
        sql = (
            f'INSERT INTO "{table}" ({", ".join(f'"{n}"' for n in names)}) '
            f"VALUES ({', '.join(placeholders)}) RETURNING *"
        )
        params = [_encode(row[name], columns[name].udt_name) for name in names]
        return await self.conn.fetchrow(sql, *params)

    async def insert_many(self, table: str, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            await self.insert(table, **row)

    async def clone(
        self, table: str, row_id: Any, count: int, overrides: dict[str, str], key: str = "id"
    ) -> None:
        """Insert ``count`` copies of the row whose ``key`` column is ``row_id``.

        ``overrides`` maps a column to a SQL expression; ``g`` is the copy number.
        """
        names = [c.name for c in self._columns[table]]
        exprs = [overrides.get(name, f't."{name}"') for name in names]
        await self.conn.execute(
            f'INSERT INTO "{table}" ({", ".join(f'"{n}"' for n in names)}) '
            f'SELECT {", ".join(exprs)} FROM "{table}" t, generate_series(1, $2) g '
            f'WHERE t."{key}" = $1',
            row_id,
            count,
        )

    async def fill(self, table: str, column: Column) -> Any:
        """A value for a NOT NULL column the caller does not name."""
        fk = self._foreign_keys.get((table, column.name))
        if fk is not None:
            dst_table, dst_column = fk
            # A unique column takes a random parent so that repeated rows can differ.
            order = "random()" if self.is_unique(table, column.name) else "1"
            value = await self.conn.fetchval(
                f'SELECT "{dst_column}" FROM "{dst_table}" ORDER BY {order} LIMIT 1'
            )
            if value is None:
                raise LookupError(f"{table}.{column.name} needs a row in {dst_table} first")
            return value
        if self.is_unique(table, column.name) and column.udt_name in {"int2", "int4", "int8"}:
            return secrets.randbelow(32000) + 1
        value = _placeholder(column.udt_name, self.allowed_values(table, column))
        if isinstance(value, str) and column.max_length is not None:
            # Keep the random tail, which makes the value unique.
            return value[-column.max_length :]
        return value


def _cast(udt_name: str) -> str:
    if udt_name.startswith("_"):
        return f'"{udt_name[1:]}"[]'
    return f'"{udt_name}"'


def _encode(value: Any, udt_name: str) -> Any:
    if value is None:
        return None
    if udt_name == "uuid" and isinstance(value, str):
        return uuid.UUID(value)
    if udt_name in {"varchar", "text", "bpchar"} and not isinstance(value, str):
        return str(value)
    if udt_name in {"int2", "int4", "int8"} and isinstance(value, str):
        return int(value)
    if udt_name.startswith("_") and isinstance(value, (list, tuple)):
        return list(value)
    return value


def _placeholder(udt_name: str, enum_labels: list[str] | None) -> Any:
    if enum_labels:
        return enum_labels[0]
    now = datetime.datetime.now(datetime.UTC)
    match udt_name:
        case "uuid":
            return uuid.uuid4()
        case "varchar" | "text" | "bpchar" | "citext":
            return f"seed-{uuid.uuid4().hex[:12]}"
        case "int2" | "int4" | "int8":
            return 0
        case "numeric" | "float4" | "float8":
            return 0
        case "bool":
            return False
        case "timestamptz" | "timestamp":
            return now
        case "date":
            return now.date()
        case "interval":
            return datetime.timedelta(0)
        case "json" | "jsonb":
            return {}
        case "bytea":
            return b""
        case "inet" | "cidr":
            return "127.0.0.1"
    if udt_name.startswith("_"):
        return []
    raise TypeError(f"no placeholder for column type {udt_name}")
