"""Write primitives every v2 write concern shares.

Row insert/delete/upsert with spec-declared check execution, integrity-error
parsing and matching, and membership recording/removal with the transitional
dual-write. No public operation lives here — the per-concern write ops inherit
these on top of :class:`~.base.V2OpsBase`.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Collection, Mapping, Sequence
from typing import Any, ClassVar, NoReturn, cast

import sqlalchemy as sa
from asyncpg.exceptions import PostgresError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
)
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.manager.errors.permission import VirtualEntityNotFound
from ai.backend.manager.errors.repository import (
    CheckConstraintViolationError,
    ExclusionViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    RepositoryIntegrityError,
    UniqueConstraintViolationError,
    UpsertEmptyResultError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.specs.membership import EntityMembershipEntry
from ai.backend.manager.models.specs.types import ConflictCheck, IntegrityErrorCheck
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.base import V2OpsBase


class V2WriteOpsBase(V2OpsBase):
    """The shared write primitives, bound to a single session."""

    async def _provision_entities(self, entities: Sequence[EntityIdentifier]) -> None:
        """Put each entity into the RBAC graph: its virtual entity node, its self
        entity-membership and its self scope-binding (permission_cap NULL). The reverse
        of :meth:`_teardown_entity`. Idempotent: an existing node is a no-op."""
        if not entities:
            return
        values = [{"entity_type": e.entity_type(), "entity_id": e} for e in entities]
        insert_stmt = (
            pg_insert(VirtualEntityRow)
            .values(values)
            .on_conflict_do_nothing(index_elements=["entity_type", "entity_id"])
            .returning(
                VirtualEntityRow.id,
                VirtualEntityRow.entity_type,
                VirtualEntityRow.entity_id,
            )
        )
        inserted = (await self._sess.execute(insert_stmt)).all()
        if not inserted:
            return
        membership_stmt = (
            pg_insert(EntityMembershipRow)
            .values([
                {
                    "virtual_entity_id": row.id,
                    "member_entity_id": row.id,
                    "permission_cap": None,
                }
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(membership_stmt)
        binding_stmt = (
            pg_insert(ScopeBindingRow)
            .values([
                {
                    "virtual_entity_id": row.id,
                    "scope_entity_id": row.id,
                    "permission_cap": None,
                }
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(binding_stmt)

    async def _teardown_entity(self, entity: EntityIdentifier) -> None:
        """Remove what the entity left: permissions granted on it, its virtual entity
        node (every edge naming the node goes with it by FK), and the labels put on it.

        The permission delete keys on the id alone, which is a UUID and so already
        names one entity; the type would only narrow it to what it already is.
        """
        await self._sess.execute(
            sa.delete(PermissionRow).where(PermissionRow.scope_id == str(entity))
        )
        await self._sess.execute(
            sa.delete(VirtualEntityRow).where(
                VirtualEntityRow.entity_type == entity.entity_type(),
                VirtualEntityRow.entity_id == entity,
            )
        )
        await self._sess.execute(
            sa.delete(EntityLabelRow).where(
                EntityLabelRow.entity_type == entity.entity_type(),
                EntityLabelRow.entity_id == entity,
            )
        )

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
        await self._insert_rows((row,), checks)

    async def _insert_rows(
        self, rows: Sequence[Base], checks: Sequence[IntegrityErrorCheck]
    ) -> None:
        """Flush rows in one batch, then read back whatever the database computed.

        Each row is refreshed on its own: the values differ per row, and ``refresh``
        is what keeps composite keys and the identity map right. Rows that left
        nothing to SQL — every ordinary insert — are skipped, so this costs nothing
        until a spec asks for it.
        """
        computed = [self._sql_valued_columns(row) for row in rows]
        self._sess.add_all(rows)
        try:
            await self._sess.flush()
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)
        for row, names in zip(rows, computed, strict=True):
            if names:
                await self._sess.refresh(row, names)

    def _sql_valued_columns(self, row: Base) -> list[str]:
        """The columns the spec left to SQL, read before the insert.

        A value given as an expression is computed by the database, so reading it back
        needs a SELECT — and after the flush the attribute is expired, which in an
        async session raises rather than loading.
        """
        return [
            attr.key
            for attr in sa.inspect(type(row)).column_attrs
            if isinstance(getattr(row, attr.key, None), sa.sql.ColumnElement)
        ]

    async def _update_row_returning[TRow: Base](
        self,
        row_class: type[TRow],
        id_column: InstrumentedAttribute[Any],
        id_value: Any,
        values: dict[str, Any],
        checks: Sequence[IntegrityErrorCheck],
    ) -> TRow | None:
        """Update the row the id names and return it; ``None`` if no row matched.

        With nothing to set, reads the current row instead, so callers can tell
        "nothing to change" apart from "row not found".
        """
        table = row_class.__table__
        if not values:
            existing = await self._sess.execute(sa.select(row_class).where(id_column == id_value))
            return existing.scalar_one_or_none()
        stmt = (
            sa.update(table).values(values).where(id_column == id_value).returning(*table.columns)
        )
        # from_statement lets SQLAlchemy map the RETURNING columns onto the ORM class.
        select_stmt = sa.select(row_class).from_statement(stmt)
        try:
            result = await self._sess.execute(select_stmt)
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)
        return result.scalar_one_or_none()

    async def _update_guarded_row_returning[TRow: Base](
        self,
        row_class: type[TRow],
        id_column: InstrumentedAttribute[Any],
        id_value: Any,
        guards: Sequence[Callable[[], sa.sql.expression.ColumnElement[bool]]],
        values: dict[str, Any],
        checks: Sequence[IntegrityErrorCheck],
    ) -> TRow | None:
        """Update the row the id names while its guards hold; ``None`` if none matched.

        The guards ride on the statement, so no separate read and no row lock stand
        between the check and the write. With nothing to set, reads the current row
        instead, so callers can tell "nothing to change" apart from "row not found".
        """
        table = row_class.__table__
        if not values:
            existing = await self._sess.execute(sa.select(row_class).where(id_column == id_value))
            return existing.scalar_one_or_none()
        stmt = sa.update(table).values(values).where(id_column == id_value)
        for guard in guards:
            stmt = stmt.where(guard())
        # from_statement lets SQLAlchemy map the RETURNING columns onto the ORM class.
        select_stmt = sa.select(row_class).from_statement(stmt.returning(*table.columns))
        try:
            result = await self._sess.execute(select_stmt)
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)
        return result.scalar_one_or_none()

    async def _delete_row_returning[TRow: Base](
        self, row_class: type[TRow], id_column: InstrumentedAttribute[Any], id_value: Any
    ) -> TRow | None:
        table = row_class.__table__
        stmt = sa.delete(table).where(id_column == id_value).returning(*table.columns)
        # from_statement lets SQLAlchemy map the RETURNING columns onto the ORM class.
        # Calling the row class instead would go through its __init__, which many rows
        # narrow to the caller-supplied columns — a server-generated one then arrives as
        # an unexpected keyword and the purge fails on rows it can read back perfectly.
        select_stmt = sa.select(row_class).from_statement(stmt)
        try:
            result = await self._sess.execute(select_stmt)
        except sa.exc.IntegrityError as e:
            raise self._parse_integrity_error(e) from e
        return result.scalar_one_or_none()

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

    async def _record_memberships(self, entries: Sequence[EntityMembershipEntry]) -> None:
        """Record declared memberships in the parents' virtual entities, idempotently;
        a parent or member without a virtual entity fails (resolve-or-fail)."""
        if not entries:
            return
        node_ids = await self._resolve_virtual_entity_ids([
            *(e.parent for e in entries),
            *(e.member for e in entries),
        ])
        await self._bulk_insert_ignore_conflicts(
            [
                EntityMembershipRow(
                    virtual_entity_id=node_ids[(entry.parent.entity_type(), entry.parent)],
                    member_entity_id=node_ids[(entry.member.entity_type(), entry.member)],
                    permission_cap=None,
                )
                for entry in entries
            ],
        )

    async def _remove_memberships(self, members: Sequence[EntityIdentifier]) -> None:
        """Remove every membership the members hold, so a purge cannot leave
        orphan registrations behind."""
        if not members:
            return
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.member_entity_id.in_(self._virtual_entity_ids_query(members))
            )
        )

    def _virtual_entity_ids_query(
        self, entities: Sequence[EntityIdentifier]
    ) -> sa.Select[tuple[VirtualEntityID]]:
        """The ids of the entities' virtual entity nodes; an entity without one
        contributes nothing, so a delete keyed on it matches nothing."""
        return sa.select(VirtualEntityRow.id).where(
            sa.tuple_(VirtualEntityRow.entity_type, VirtualEntityRow.entity_id).in_([
                (e.entity_type(), e) for e in entities
            ])
        )

    async def _resolve_virtual_entity_ids(
        self, entities: Sequence[EntityIdentifier]
    ) -> dict[tuple[EntityType, uuid.UUID], VirtualEntityID]:
        """Resolve-or-fail, never get-or-create: a declared parent without a virtual
        scope raises :class:`VirtualEntityNotFound` naming every missing scope."""
        stmt = sa.select(
            VirtualEntityRow.entity_type,
            VirtualEntityRow.entity_id,
            VirtualEntityRow.id,
        ).where(
            sa.tuple_(VirtualEntityRow.entity_type, VirtualEntityRow.entity_id).in_([
                (e.entity_type(), e) for e in entities
            ])
        )
        resolved = {
            (row.entity_type, row.entity_id): row.id
            for row in (await self._sess.execute(stmt)).all()
        }
        missing = [e for e in entities if (e.entity_type(), e) not in resolved]
        if missing:
            raise VirtualEntityNotFound(
                "No virtual entity for entities: "
                + ", ".join(f"{e.entity_type()}:{e}" for e in missing)
            )
        return resolved

    async def _batch_purge_returning[TRow: Base, TData](
        self,
        scope_condition: sa.ColumnElement[bool] | None,
        build_subquery: Callable[[], sa.sql.Select[Any]],
        conflict_checks: Sequence[ConflictCheck],
        to_data: Callable[[TRow], TData],
        batch_size: int = 1000,
    ) -> list[TData]:
        base_subquery = build_subquery()
        entity = base_subquery.column_descriptions[0]["entity"]
        table = sa.inspect(entity).local_table
        pk_columns = list(table.primary_key.columns)
        row_class = cast("type[TRow]", entity)

        await self._validate_conflict_checks(conflict_checks)

        removed: list[TData] = []
        while True:
            selecting = build_subquery()
            if scope_condition is not None:
                selecting = selecting.where(scope_condition)
            sub = selecting.subquery()
            pk_subquery = sa.select(*[sub.c[pk.key] for pk in pk_columns]).limit(batch_size)
            stmt = (
                sa.delete(table)
                .where(sa.tuple_(*pk_columns).in_(pk_subquery))
                .returning(*table.columns)
            )
            try:
                result = await self._sess.execute(stmt)
            except sa.exc.IntegrityError as e:
                raise self._parse_integrity_error(e) from e
            rows = result.fetchall()
            removed.extend(to_data(row_class(**dict(r._mapping))) for r in rows)
            if len(rows) < batch_size:
                break
        return removed
