"""Write primitives every v2 write concern shares.

Row insert/delete/upsert with spec-declared check execution, integrity-error
parsing and matching, membership recording/removal with the transitional
dual-write, and the legacy type conversions. No public operation lives here —
the per-concern write ops inherit these on top of :class:`~.base.V2OpsBase`.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import Any, ClassVar, NoReturn

import sqlalchemy as sa
from asyncpg.exceptions import PostgresError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityRef, EntityType, ScopeRef, ScopeType
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.errors.permission import VirtualScopeNotFound
from ai.backend.manager.errors.repository import (
    CheckConstraintViolationError,
    ExclusionViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    RepositoryIntegrityError,
    UniqueConstraintViolationError,
    UnsupportedCompositePrimaryKeyError,
    UpsertEmptyResultError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.membership import ScopeMembershipEntry
from ai.backend.manager.models.specs.types import ConflictCheck, IntegrityErrorCheck
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.base import V2OpsBase


class V2WriteOpsBase(V2OpsBase):
    """The shared write primitives, bound to a single session."""

    _SQLSTATE_TO_ERROR: ClassVar[Mapping[str, type[RepositoryIntegrityError]]] = {
        "23505": UniqueConstraintViolationError,
        "23503": ForeignKeyViolationError,
        "23514": CheckConstraintViolationError,
        "23502": NotNullViolationError,
        "23P01": ExclusionViolationError,
    }

    _MESSAGE_KEYWORDS: ClassVar[Sequence[tuple[str, type[RepositoryIntegrityError]]]] = (
        ("unique constraint", UniqueConstraintViolationError),
        ("unique violation", UniqueConstraintViolationError),
        ("foreign key", ForeignKeyViolationError),
        ("not-null constraint", NotNullViolationError),
        ("null value in column", NotNullViolationError),
        ("check constraint", CheckConstraintViolationError),
        ("exclusion constraint", ExclusionViolationError),
    )

    async def _validate_conflict_checks(self, checks: Sequence[ConflictCheck]) -> None:
        """Validate the spec-declared conflict checks in a single query, raising the
        first failing check's error. The declarations live in ``models/specs``; this
        provider is their only executor on the v2 path."""
        if not checks:
            return
        select_clauses = [
            sa.exists().where(check.condition()).label(f"conflict_{i}")
            for i, check in enumerate(checks)
        ]
        result = await self._sess.execute(sa.select(*select_clauses))
        row = result.mappings().one()
        for i, check in enumerate(checks):
            if row[f"conflict_{i}"]:
                raise check.error

    def _parse_integrity_error(self, e: sa.exc.IntegrityError) -> RepositoryIntegrityError:
        """Parse a SQLAlchemy IntegrityError into a structured RepositoryIntegrityError.

        Classification: the SQLSTATE code from asyncpg first, keyword matching on the
        message as fallback. Diagnostic attributes (constraint_name, table_name,
        column_name, detail) come from asyncpg's ``PostgresError`` when available.
        """
        orig = e.orig
        pgcode: str | None = None
        constraint_name: str | None = None
        table_name: str | None = None
        column_name: str | None = None
        detail: str | None = None

        # SA asyncpg dialect wraps the asyncpg PostgresError in a dbapi-level
        # IntegrityError. The original asyncpg error is chained as __cause__.
        pg_error: PostgresError | None = None
        if isinstance(orig, PostgresError):
            pg_error = orig
        elif orig is not None and isinstance(orig.__cause__, PostgresError):
            pg_error = orig.__cause__

        if pg_error is not None:
            pgcode = pg_error.sqlstate
            constraint_name = pg_error.constraint_name
            table_name = pg_error.table_name
            column_name = pg_error.column_name
            detail = pg_error.detail

        error_msg = str(e.orig) if e.orig is not None else str(e)
        kwargs = {
            "constraint_name": constraint_name,
            "table_name": table_name,
            "column_name": column_name,
            "detail": detail,
            "pgcode": pgcode,
        }

        if pgcode is not None:
            error_cls = self._SQLSTATE_TO_ERROR.get(pgcode)
            if error_cls is not None:
                return error_cls(extra_msg=error_msg, **kwargs)

        msg_lower = error_msg.lower()
        for keyword, keyword_error_cls in self._MESSAGE_KEYWORDS:
            if keyword in msg_lower:
                return keyword_error_cls(extra_msg=error_msg, **kwargs)

        return RepositoryIntegrityError(extra_msg=error_msg, **kwargs)

    def _match_integrity_error(
        self,
        parsed: RepositoryIntegrityError,
        checks: Sequence[IntegrityErrorCheck],
    ) -> NoReturn:
        """Match a parsed integrity error against the spec-declared checks and raise
        the first matching domain error; without a match, the parsed error itself."""
        for check in checks:
            if not isinstance(parsed, check.violation_type):
                continue
            if (
                check.constraint_name is not None
                and parsed.constraint_name != check.constraint_name
            ):
                continue
            raise check.error from parsed
        raise parsed

    async def _insert_row(self, row: Base, checks: Sequence[IntegrityErrorCheck]) -> None:
        self._sess.add(row)
        try:
            await self._sess.flush()
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)

    async def _update_row_returning[TRow: Base](
        self,
        row_class: type[TRow],
        pk_value: Any,
        values: dict[str, Any],
        checks: Sequence[IntegrityErrorCheck],
    ) -> TRow | None:
        """Update one row by primary key and return it; ``None`` if no row matched.

        With nothing to set, reads the current row instead, so callers can tell
        "nothing to change" apart from "row not found".
        """
        table = row_class.__table__
        pk_columns = list(table.primary_key.columns)
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Updater only supports single-column primary keys (table: {table.name})",
            )
        if not values:
            existing = await self._sess.execute(
                sa.select(row_class).where(pk_columns[0] == pk_value)
            )
            return existing.scalar_one_or_none()
        stmt = (
            sa.update(table)
            .values(values)
            .where(pk_columns[0] == pk_value)
            .returning(*table.columns)
        )
        # from_statement lets SQLAlchemy map the RETURNING columns onto the ORM class.
        select_stmt = sa.select(row_class).from_statement(stmt)
        try:
            result = await self._sess.execute(select_stmt)
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)
        return result.scalar_one_or_none()

    async def _delete_row_returning[TRow: Base](
        self, row_class: type[TRow], pk_value: Any
    ) -> TRow | None:
        table = row_class.__table__
        pk_columns = list(table.primary_key.columns)
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Purger only supports single-column primary keys (table: {table.name})",
            )
        stmt = sa.delete(table).where(pk_columns[0] == pk_value).returning(*table.columns)
        try:
            result = await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            raise self._parse_integrity_error(e) from e
        row_data = result.fetchone()
        if row_data is None:
            return None
        row: TRow = row_class(**dict(row_data._mapping))
        return row

    async def _upsert_row_returning[TRow: Base](
        self,
        row_class: type[TRow],
        index_elements: list[str],
        insert_values: dict[str, Any],
        update_values: dict[str, Any],
        checks: Sequence[IntegrityErrorCheck],
    ) -> TRow:
        table = row_class.__table__
        stmt = (
            pg_insert(table)
            .values(insert_values)
            .on_conflict_do_update(index_elements=index_elements, set_=update_values)
            .returning(*table.columns)
        )
        try:
            result = await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)
        row_data = result.fetchone()
        if row_data is None:
            raise UpsertEmptyResultError
        row: TRow = row_class(**dict(row_data._mapping))
        return row

    async def _bulk_insert_ignore_conflicts(self, rows: Collection[Base]) -> None:
        """Insert the given rows in one statement, skipping rows that conflict with
        existing ones (``ON CONFLICT DO NOTHING``); existing rows are kept as-is."""
        if not rows:
            return
        row_cls = type(next(iter(rows)))
        mapper = sa.inspect(row_cls)
        column_keys = {c.key for c in mapper.columns}
        values_list = [{k: v for k, v in row.__dict__.items() if k in column_keys} for row in rows]
        stmt = pg_insert(row_cls).values(values_list).on_conflict_do_nothing()
        await self._sess.execute(stmt)
        await self._sess.flush()

    async def _record_memberships(self, entries: Sequence[ScopeMembershipEntry]) -> None:
        """Record declared memberships in the parents' virtual scopes, idempotently;
        a declared parent without a virtual scope fails (resolve-or-fail)."""
        if not entries:
            return
        scope_ids = await self._resolve_virtual_scope_ids([e.parent_scope for e in entries])
        await self._bulk_insert_ignore_conflicts(
            [
                EntityMembershipRow(
                    virtual_scope_id=scope_ids[entry.parent_scope],
                    entity_type=entry.member.entity_type,
                    entity_id=entry.member.entity_id,
                    permission_cap=None,
                )
                for entry in entries
            ],
        )

    async def _remove_memberships(self, members: Sequence[EntityRef]) -> None:
        """Remove every membership the members hold, so a purge cannot leave
        orphan registrations behind."""
        if not members:
            return
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                sa.tuple_(EntityMembershipRow.entity_type, EntityMembershipRow.entity_id).in_([
                    (m.entity_type, m.entity_id) for m in members
                ])
            )
        )

    async def _resolve_virtual_scope_ids(
        self, scopes: Sequence[ScopeRef]
    ) -> dict[ScopeRef, VirtualScopeID]:
        """Resolve-or-fail, never get-or-create: a declared parent without a virtual
        scope raises :class:`VirtualScopeNotFound` naming every missing scope."""
        stmt = sa.select(
            VirtualScopeRow.scope_type,
            VirtualScopeRow.scope_id,
            VirtualScopeRow.id,
        ).where(
            sa.tuple_(VirtualScopeRow.scope_type, VirtualScopeRow.scope_id).in_([
                (s.scope_type, s.scope_id) for s in scopes
            ])
        )
        resolved = {
            ScopeRef(
                scope_type=ScopeType(EntityType(row.scope_type)), scope_id=row.scope_id
            ): row.id
            for row in (await self._sess.execute(stmt)).all()
        }
        missing = [s for s in scopes if s not in resolved]
        if missing:
            raise VirtualScopeNotFound(
                "No virtual scope for scopes: "
                + ", ".join(f"{s.scope_type}:{s.scope_id}" for s in missing)
            )
        return resolved
