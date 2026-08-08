"""V2 DB ops provider.

Executes the v2 write specs (``models/specs/``): the spec declares what to write —
row, membership, checks — and this layer performs it. Self-contained on purpose —
nothing here inherits from the legacy provider, and only the data-returning read
paths exist, so a domain handed this provider cannot reach any legacy path and
removing the legacy provider later touches nothing here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityRef, EntityType, ScopeRef, ScopeType
from ai.backend.common.exception import RBACTypeConversionError
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.data.permission.types import (
    EntityType as LegacyEntityType,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as LegacyScopeType,
)
from ai.backend.manager.errors.permission import VirtualScopeNotFound
from ai.backend.manager.errors.repository import (
    AmbiguousEntityKeyError,
    EmptySearchScopeError,
    UnsupportedCompositePrimaryKeyError,
    UpsertEmptyResultError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.models.specs.creator import (
    FieldEntityCreator,
    GlobalEntityCreator,
    ScopedEntityCreator,
)
from ai.backend.manager.models.specs.membership import ScopeMembershipEntry
from ai.backend.manager.models.specs.purger import (
    FieldEntityPurger,
    GlobalEntityPurger,
    ScopedEntityPurger,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import GlobalEntityUpserter, ScopedEntityUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.base.integrity import (
    match_integrity_error,
    parse_integrity_error,
)
from ai.backend.manager.repositories.base.purger import validate_conflict_checks
from ai.backend.manager.repositories.base.querier import (
    DataFinder,
    DataQuerier,
    Querier,
    execute_batch_querier,
    execute_querier,
)
from ai.backend.manager.repositories.base.rbac.utils import bulk_insert_on_conflict_do_nothing
from ai.backend.manager.repositories.base.searcher import Searcher, SearcherResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


class V2ReadOps:
    """Read-only operations bound to a single session; data-returning paths only."""

    _sess: SASession

    def __init__(self, sess: SASession) -> None:
        self._sess = sess

    async def query_data[TRow: Base, TData](
        self, querier: DataQuerier[TRow, TData]
    ) -> TData | None:
        """Fetch a single row by primary key and return it as its ``data/`` type."""
        result = await execute_querier(
            self._sess, Querier(row_class=querier.row_class(), pk_value=querier.pk_value())
        )
        if result is None:
            return None
        return querier.to_data(result.row)

    async def find_data[TRow: Base, TData](self, finder: DataFinder[TRow, TData]) -> TData | None:
        """Fetch one row by a key that is not its primary key, as its ``data/`` type.

        Reads at most two rows and rejects the second: a lookup key is expected to
        be unique, so more than one match means the conditions are wrong or the
        constraint that should enforce it is missing.
        """
        row_class = finder.row_class()
        query = sa.select(row_class)
        for condition in finder.conditions():
            query = query.where(condition())
        result = await self._sess.execute(query.limit(2))
        rows = result.scalars().all()
        if not rows:
            return None
        if len(rows) > 1:
            raise AmbiguousEntityKeyError(
                f"The given key matches more than one {row_class.__name__}"
            )
        return finder.to_data(rows[0])

    async def search_with_scopes[TRow: Base, TData](
        self,
        scopes: Sequence[SearchScope],
        searcher: Searcher[TRow, TData],
    ) -> SearcherResult[TData]:
        """Run a searcher restricted to the given scopes; at least one is required."""
        if not scopes:
            raise EmptySearchScopeError(
                "search_with_scopes requires at least one scope; "
                "use search_in_global for an explicit unscoped global search."
            )
        return await self._search(searcher, scopes)

    async def search_in_global[TRow: Base, TData](
        self,
        searcher: Searcher[TRow, TData],
    ) -> SearcherResult[TData]:
        """Run a searcher across the entire table, with NO scope filter.

        Permitted only for callers that already hold full authority — superadmin
        endpoints or internal system operations.
        """
        return await self._search(searcher, ())

    async def _search[TRow: Base, TData](
        self,
        searcher: Searcher[TRow, TData],
        scopes: Sequence[SearchScope],
    ) -> SearcherResult[TData]:
        result = await execute_batch_querier(self._sess, searcher.build_select(), searcher, scopes)
        return SearcherResult(
            items=[searcher.to_data(row) for row in result.rows],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )


class V2WriteOps(V2ReadOps):
    """Read-write operations over the v2 write specs, bound to a single session."""

    async def create_global_entity[TRow: Base, TData](
        self, creator: GlobalEntityCreator[TRow, TData]
    ) -> TData:
        """Insert one row of a global entity."""
        row = creator.build_row()
        await self._insert_row(row, creator.integrity_error_checks())
        return creator.to_data(row)

    async def create_scoped_entity[TRow: Base, TData](
        self, creator: ScopedEntityCreator[TRow, TData]
    ) -> TData:
        """Insert one row and register it under its declared parent scope."""
        row = creator.build_row()
        await self._insert_row(row, creator.integrity_error_checks())
        await self._record_memberships([creator.membership().membership_of(row)])
        return creator.to_data(row)

    async def create_field_entity[TOwnerID: EntityID, TRow: Base, TData](
        self, creator: FieldEntityCreator[TOwnerID, TRow, TData], owner_id: TOwnerID
    ) -> TData:
        """Insert one field row under its owner's settled identifier."""
        row = creator.build_row(owner_id)
        await self._insert_row(row, creator.integrity_error_checks())
        return creator.to_data(row)

    async def bulk_create_field_entities[TOwnerID: EntityID, TRow: Base, TData](
        self, creators: Sequence[FieldEntityCreator[TOwnerID, TRow, TData]], owner_id: TOwnerID
    ) -> list[TData]:
        """Insert field rows sharing one owner, atomically in a single flush."""
        if not creators:
            return []
        rows = [creator.build_row(owner_id) for creator in creators]
        self._sess.add_all(rows)
        try:
            await self._sess.flush()
        except sa.exc.IntegrityError as e:
            # Use first creator's checks (all specs share the same creator subclass)
            match_integrity_error(parse_integrity_error(e), creators[0].integrity_error_checks())
        return [creator.to_data(row) for creator, row in zip(creators, rows, strict=True)]

    async def purge_global_entity[TRow: Base, TData](
        self, purger: GlobalEntityPurger[TRow, TData]
    ) -> TData | None:
        """Delete one row of a global entity; ``None`` if already gone."""
        await validate_conflict_checks(self._sess, purger.conflict_checks())
        row = await self._delete_row_returning(purger.row_class(), purger.pk_value())
        if row is None:
            return None
        return purger.to_data(row)

    async def purge_field_entity[TRow: Base, TData](
        self, purger: FieldEntityPurger[TRow, TData]
    ) -> TData | None:
        """Delete one field row; ``None`` if already gone. No membership involved —
        the delete is authorized through the owner."""
        await validate_conflict_checks(self._sess, purger.conflict_checks())
        row = await self._delete_row_returning(purger.row_class(), purger.pk_value())
        if row is None:
            return None
        return purger.to_data(row)

    async def purge_scoped_entity[TRow: Base, TData](
        self, purger: ScopedEntityPurger[TRow, TData]
    ) -> TData | None:
        """Delete one row and remove its declared membership, symmetrically with
        :meth:`create_scoped_entity`; ``None`` if already gone."""
        await validate_conflict_checks(self._sess, purger.conflict_checks())
        row = await self._delete_row_returning(purger.row_class(), purger.pk_value())
        if row is None:
            return None
        await self._remove_memberships([purger.membership().membership_of(row).member])
        return purger.to_data(row)

    async def upsert_global_entity[TRow: Base, TData](
        self, upserter: GlobalEntityUpserter[TRow, TData]
    ) -> TData:
        """Insert or update on conflict, for a global entity."""
        row = await self._upsert_row_returning(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(),
            upserter.build_update_values(),
            upserter.integrity_error_checks(),
        )
        return upserter.to_data(row)

    async def upsert_scoped_entity[TRow: Base, TData](
        self, upserter: ScopedEntityUpserter[TRow, TData]
    ) -> TData:
        """Insert or update on conflict, registering the resulting row under the
        create rule; the registration is idempotent for the update case."""
        row = await self._upsert_row_returning(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(),
            upserter.build_update_values(),
            upserter.integrity_error_checks(),
        )
        await self._record_memberships([upserter.membership().membership_of(row)])
        return upserter.to_data(row)

    async def _insert_row(self, row: Base, checks: Sequence[IntegrityErrorCheck]) -> None:
        self._sess.add(row)
        try:
            await self._sess.flush()
        except sa.exc.IntegrityError as e:
            match_integrity_error(parse_integrity_error(e), checks)

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
            raise parse_integrity_error(e) from e
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
            match_integrity_error(parse_integrity_error(e), checks)
        row_data = result.fetchone()
        if row_data is None:
            raise UpsertEmptyResultError
        row: TRow = row_class(**dict(row_data._mapping))
        return row

    async def _record_memberships(self, entries: Sequence[ScopeMembershipEntry]) -> None:
        """Record declared memberships: the parent's virtual scope (resolve-or-fail)
        plus the legacy association, both idempotently (transitional dual-write)."""
        if not entries:
            return
        scope_ids = await self._resolve_virtual_scope_ids([e.parent_scope for e in entries])
        await bulk_insert_on_conflict_do_nothing(
            self._sess,
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
        await bulk_insert_on_conflict_do_nothing(
            self._sess,
            [
                AssociationScopesEntitiesRow(
                    scope_type=self._legacy_scope_type(entry.parent_scope.scope_type),
                    scope_id=str(entry.parent_scope.scope_id),
                    entity_type=self._legacy_entity_type(entry.member.entity_type),
                    entity_id=str(entry.member.entity_id),
                )
                for entry in entries
            ],
        )

    async def _remove_memberships(self, members: Sequence[EntityRef]) -> None:
        """Remove every membership and legacy association the members hold, so a
        purge cannot leave orphan registrations behind."""
        if not members:
            return
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                sa.tuple_(EntityMembershipRow.entity_type, EntityMembershipRow.entity_id).in_([
                    (m.entity_type, m.entity_id) for m in members
                ])
            )
        )
        await self._sess.execute(
            sa.delete(AssociationScopesEntitiesRow).where(
                sa.tuple_(
                    AssociationScopesEntitiesRow.entity_type,
                    AssociationScopesEntitiesRow.entity_id,
                ).in_([
                    (self._legacy_entity_type(m.entity_type), str(m.entity_id)) for m in members
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
            ScopeRef(scope_type=ScopeType(row.scope_type), scope_id=row.scope_id): row.id
            for row in (await self._sess.execute(stmt)).all()
        }
        missing = [s for s in scopes if s not in resolved]
        if missing:
            raise VirtualScopeNotFound(
                "No virtual scope for scopes: "
                + ", ".join(f"{s.scope_type}:{s.scope_id}" for s in missing)
            )
        return resolved

    def _legacy_scope_type(self, scope_type: ScopeType) -> LegacyScopeType:
        try:
            return LegacyScopeType(scope_type)
        except ValueError as e:
            raise RBACTypeConversionError(
                f"Scope type {scope_type!r} has no legacy scope type for the dual-write"
            ) from e

    def _legacy_entity_type(self, entity_type: EntityType) -> LegacyEntityType:
        try:
            return LegacyEntityType(entity_type)
        except ValueError as e:
            raise RBACTypeConversionError(
                f"Entity type {entity_type!r} has no legacy entity type for the dual-write"
            ) from e


class V2DBOpsProvider:
    """Hands out session-bound ops over the v2 specs; the engine stays private."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @asynccontextmanager
    async def read_ops(self) -> AsyncIterator[V2ReadOps]:
        """Open a read-only transaction and yield read-only ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield V2ReadOps(sess)

    @asynccontextmanager
    async def write_ops(self) -> AsyncIterator[V2WriteOps]:
        """Open a read-write transaction and yield the v2 write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2WriteOps(sess)
