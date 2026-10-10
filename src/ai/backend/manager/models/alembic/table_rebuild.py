from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.engine import Connection


@dataclass(frozen=True)
class _Reference:
    table: str
    name: str
    definition: str
    columns: list[str]
    referenced_columns: list[str]


class TableRebuild:
    """Replaces a table with a new one the caller fills.

    Keys, indexes and the foreign keys pointing at the table are read from the current
    table and built again after the copy. Rows left without a referenced row are deleted.
    """

    _conn: Connection
    _table: str
    _new_table: str
    _constraints: list[tuple[str, str]]
    _indexes: list[str]
    _references: list[_Reference]

    def __init__(self, conn: Connection, table: str) -> None:
        self._conn = conn
        self._table = table
        self._new_table = f"{table}_new"
        self._constraints = []
        self._indexes = []
        self._references = []

    @property
    def new_table(self) -> str:
        return self._new_table

    def columns(self) -> dict[str, str]:
        """Maps each column of the current table to its type, in column order."""
        rows = self._conn.execute(
            sa.text(
                "SELECT attname, format_type(atttypid, atttypmod) FROM pg_attribute"
                " WHERE attrelid = CAST(:table AS regclass) AND attnum > 0 AND NOT attisdropped"
                " ORDER BY attnum"
            ).bindparams(table=self._table)
        )
        return {name: type_ for name, type_ in rows}

    def quote(self, name: str) -> str:
        return self._conn.dialect.identifier_preparer.quote(name)

    def create_new_table(self) -> None:
        """Drops the foreign keys pointing at the table and creates an empty copy of it."""
        self._read_definitions()
        for reference in self._references:
            self._conn.execute(
                sa.text(
                    f"ALTER TABLE {reference.table} DROP CONSTRAINT {self.quote(reference.name)}"
                )
            )
        self._conn.execute(
            sa.text(
                f"CREATE TABLE {self._new_table}"
                f" (LIKE {self._table} INCLUDING DEFAULTS INCLUDING CONSTRAINTS)"
            )
        )

    def replace(self) -> None:
        """Drops the current table, renames the new one and builds the keys and indexes on it."""
        self._conn.execute(sa.text(f"DROP TABLE {self._table}"))
        self._conn.execute(sa.text(f"ALTER TABLE {self._new_table} RENAME TO {self._table}"))
        for name, definition in self._constraints:
            self._conn.execute(
                sa.text(f"ALTER TABLE {self._table} ADD CONSTRAINT {self.quote(name)} {definition}")
            )
        for definition in self._indexes:
            self._conn.execute(sa.text(definition))
        for reference in self._references:
            self._delete_orphans(reference)
            self._conn.execute(
                sa.text(
                    f"ALTER TABLE {reference.table}"
                    f" ADD CONSTRAINT {self.quote(reference.name)} {reference.definition}"
                )
            )
        self._conn.execute(sa.text(f"ANALYZE {self._table}"))

    def _read_definitions(self) -> None:
        # Unique keys come before foreign keys so that a self-reference finds its target.
        self._constraints = [
            (name, definition)
            for name, definition in self._conn.execute(
                sa.text(
                    "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint"
                    " WHERE conrelid = CAST(:table AS regclass) AND contype IN ('p', 'u', 'x', 'f')"
                    " ORDER BY CASE contype WHEN 'f' THEN 1 ELSE 0 END, conname"
                ).bindparams(table=self._table)
            )
        ]
        self._indexes = [
            definition
            for (definition,) in self._conn.execute(
                sa.text(
                    "SELECT pg_get_indexdef(i.indexrelid) FROM pg_index i"
                    " WHERE i.indrelid = CAST(:table AS regclass) AND NOT EXISTS ("
                    "  SELECT 1 FROM pg_constraint c"
                    "  WHERE c.conrelid = i.indrelid AND c.conindid = i.indexrelid)"
                    " ORDER BY i.indexrelid::regclass::text"
                ).bindparams(table=self._table)
            )
        ]
        self._references = [
            _Reference(
                table=table,
                name=name,
                definition=definition,
                columns=list(columns),
                referenced_columns=list(referenced_columns),
            )
            for table, name, definition, columns, referenced_columns in self._conn.execute(
                sa.text(
                    "SELECT c.conrelid::regclass::text, c.conname, pg_get_constraintdef(c.oid),"
                    "  ARRAY(SELECT quote_ident(a.attname)"
                    "   FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, position)"
                    "   JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum"
                    "   ORDER BY k.position),"
                    "  ARRAY(SELECT quote_ident(a.attname)"
                    "   FROM unnest(c.confkey) WITH ORDINALITY AS k(attnum, position)"
                    "   JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = k.attnum"
                    "   ORDER BY k.position)"
                    " FROM pg_constraint c"
                    " WHERE c.confrelid = CAST(:table AS regclass) AND c.contype = 'f'"
                    "  AND c.conrelid <> c.confrelid"
                    " ORDER BY 1, 2"
                ).bindparams(table=self._table)
            )
        ]

    def _delete_orphans(self, reference: _Reference) -> None:
        present = " AND ".join(f"r.{column} IS NOT NULL" for column in reference.columns)
        matches = " AND ".join(
            f"t.{referenced} = r.{column}"
            for column, referenced in zip(
                reference.columns, reference.referenced_columns, strict=True
            )
        )
        self._conn.execute(
            sa.text(
                f"DELETE FROM {reference.table} r WHERE {present}"
                f" AND NOT EXISTS (SELECT 1 FROM {self._table} t WHERE {matches})"
            )
        )
