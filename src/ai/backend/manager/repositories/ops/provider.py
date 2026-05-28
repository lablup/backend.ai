"""DB ops provider.

Wraps an :class:`ExtendedAsyncSAEngine` and exposes a spec-only operations surface.
The engine is isolated inside :class:`DBOpsProvider`; callers obtain a session-bound
:class:`ReadOps` / :class:`WriteOps` via the ``read_ops()`` / ``write_ops()`` context
managers and never touch the engine, raw sessions, or raw SQLAlchemy statements.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, RelationType
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.errors.repository import EmptySearchScopeError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset import RolePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchPurgerResult,
    BatchPurgerSpec,
    BatchQuerier,
    BatchQuerierResult,
    BatchUpdater,
    BatchUpdaterResult,
    BulkCreator,
    BulkCreatorResult,
    BulkCreatorResultWithFailures,
    BulkPurgerResultWithFailures,
    BulkUpdaterResult,
    Creator,
    CreatorResult,
    CreatorSpec,
    DependentCreatorSpec,
    NextValuePolicy,
    Purger,
    PurgerResult,
    Querier,
    QuerierResult,
    ScopeContext,
    ScopeCreator,
    ScopeCreatorResult,
    ScopePurger,
    ScopePurgerResult,
    SearchScope,
    Updater,
    UpdaterResult,
    Upserter,
    UpserterResult,
    execute_batch_purger,
    execute_batch_querier,
    execute_batch_updater,
    execute_bulk_creator,
    execute_bulk_creator_partial,
    execute_bulk_dependent_creator,
    execute_bulk_purger_partial,
    execute_bulk_updater_partial,
    execute_creator,
    execute_dependent_creator,
    execute_next_value_creator,
    execute_purger,
    execute_querier,
    execute_updater,
    execute_upserter,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Row
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


@dataclass(frozen=True)
class _RoleScopeAssociationSpec(CreatorSpec[AssociationScopesEntitiesRow]):
    """Insert the association_scopes_entities row tying a role to its scope."""

    role_id: UUID
    scope_context: ScopeContext

    def build_row(self) -> AssociationScopesEntitiesRow:
        return AssociationScopesEntitiesRow(
            scope_type=self.scope_context.scope_type.to_scope_type(),
            scope_id=self.scope_context.scope_id,
            entity_type=EntityType.ROLE,
            entity_id=str(self.role_id),
            relation_type=RelationType.AUTO,
        )


@dataclass(frozen=True)
class _ScopePermissionsPurgeSpec(BatchPurgerSpec[PermissionRow]):
    """Select every permission row pinned to a scope, derived from its context.

    Mirrors how :meth:`ScopeWriteOps._build_permission_row_from_preset` stamps
    ``scope_type`` / ``scope_id`` onto each permission at provisioning time.
    """

    scope_context: ScopeContext

    def build_subquery(self) -> sa.sql.Select[tuple[PermissionRow]]:
        return sa.select(PermissionRow).where(
            PermissionRow.scope_type == self.scope_context.scope_type.to_scope_type(),
            PermissionRow.scope_id == self.scope_context.scope_id,
        )


@dataclass(frozen=True)
class _ScopeAssociationsPurgeSpec(BatchPurgerSpec[AssociationScopesEntitiesRow]):
    """Select every association row that references a scope, as scope or as entity.

    Role-to-scope rows reference the scope as the scope side; parent-scope rows
    (e.g. a project under its domain) reference it as the entity side. Both are
    OR-combined so a single batched delete drops the whole set.
    """

    scope_context: ScopeContext

    def build_subquery(self) -> sa.sql.Select[tuple[AssociationScopesEntitiesRow]]:
        scope_type = self.scope_context.scope_type
        scope_id = self.scope_context.scope_id
        return sa.select(AssociationScopesEntitiesRow).where(
            sa.or_(
                sa.and_(
                    AssociationScopesEntitiesRow.scope_type == scope_type.to_scope_type(),
                    AssociationScopesEntitiesRow.scope_id == scope_id,
                ),
                sa.and_(
                    AssociationScopesEntitiesRow.entity_type == scope_type.to_entity_type(),
                    AssociationScopesEntitiesRow.entity_id == scope_id,
                ),
            )
        )


@dataclass(frozen=True)
class _RoleEntry:
    """A role row and its permission rows derived from a role preset.

    Both rows are pre-built (without ``role_id`` on the permissions) by the
    collector. The orchestrator adds the role row to the session, lets the
    flush populate ``role.id``, then back-fills that id onto every permission
    row before adding them.
    """

    role: RoleRow
    permissions: list[PermissionRow]


class ReadOps:
    """Read-only operations bound to a single session.

    Input is restricted to our spec types (Querier, BatchQuerier); raw SQLAlchemy
    statements are not accepted. The bound session is private and never exposed.
    """

    _sess: SASession

    def __init__(self, sess: SASession) -> None:
        self._sess = sess

    async def query[TRow: Base](self, querier: Querier[TRow]) -> QuerierResult[TRow] | None:
        """Fetch a single row by primary key."""
        return await execute_querier(self._sess, querier)

    async def batch_query_in_global(
        self,
        query: sa.sql.Select[Any],
        querier: BatchQuerier,
    ) -> BatchQuerierResult[Row[Any]]:
        """Run a filtered/ordered/paginated query across the entire table, with NO scope filter.

        WARNING: This bypasses RBAC scope restrictions and returns rows regardless of
        ownership. It is permitted ONLY for callers that already hold full authority —
        superadmin-only endpoints or internal system operations (e.g. schedulers,
        background reconciliation). For any request acting on behalf of a regular user,
        use :meth:`batch_query_with_scopes` instead. Choosing this method is an explicit,
        auditable decision to query globally; never use it as a convenience default.
        """
        return await execute_batch_querier(self._sess, query, querier)

    async def batch_query_with_scopes(
        self,
        query: sa.sql.Select[Any],
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> BatchQuerierResult[Row[Any]]:
        """Run a filtered/ordered/paginated query restricted to the given scopes.

        At least one scope is required: an empty scope list would degrade into an
        unscoped global scan. Use :meth:`batch_query_in_global` for that, explicitly.
        """
        if not scopes:
            raise EmptySearchScopeError(
                "batch_query_with_scopes requires at least one scope; "
                "use batch_query_in_global for an explicit unscoped global query."
            )
        return await execute_batch_querier(self._sess, query, querier, scopes)


class WriteOps(ReadOps):
    """Read-write operations bound to a single session."""

    async def create[TRow: Base](self, creator: Creator[TRow]) -> CreatorResult[TRow]:
        """Insert a single row."""
        return await execute_creator(self._sess, creator)

    async def bulk_create[TRow: Base](self, bulk: BulkCreator[TRow]) -> BulkCreatorResult[TRow]:
        """Insert multiple rows atomically (all-or-nothing)."""
        return await execute_bulk_creator(self._sess, bulk)

    async def bulk_create_partial[TRow: Base](
        self,
        bulk: BulkCreator[TRow],
    ) -> BulkCreatorResultWithFailures[TRow]:
        """Insert multiple rows, isolating each via a savepoint for partial success."""
        return await execute_bulk_creator_partial(self._sess, bulk)

    async def create_dependent[TDependency, TRow: Base](
        self,
        spec: DependentCreatorSpec[TDependency, TRow],
        dependency: TDependency,
    ) -> CreatorResult[TRow]:
        """Insert a single row that depends on a resolved value (e.g. a parent id).

        The caller builds ``dependency`` from a prior operation's result and passes it
        in; the spec's ``build_row`` receives it.
        """
        return await execute_dependent_creator(self._sess, spec, dependency)

    async def bulk_create_dependent[TDependency, TRow: Base](
        self,
        specs: Sequence[DependentCreatorSpec[TDependency, TRow]],
        dependency: TDependency,
    ) -> BulkCreatorResult[TRow]:
        """Insert rows that depend on a resolved value (e.g. a just-created parent id).

        The caller builds ``dependency`` from a prior operation's result and passes it
        in; every spec's ``build_row`` receives it. Keeps each spec single-table while
        the repository coordinates the multi-table sequence.
        """
        return await execute_bulk_dependent_creator(self._sess, specs, dependency)

    async def create_with_next_value[TRow: Base](
        self,
        policy: NextValuePolicy,
        spec: DependentCreatorSpec[int, TRow],
    ) -> CreatorResult[TRow]:
        """Insert a row assigning the next monotonic column value (e.g. rank), race-free.

        Locks the parent row (FOR UPDATE), computes ``MAX(column) + gap`` within the
        scope, and inserts via the spec — all within this write transaction so the lock
        and insert commit together. Must be used inside ``write_ops()``.
        """
        return await execute_next_value_creator(self._sess, policy, spec)

    async def update[TRow: Base](self, updater: Updater[TRow]) -> UpdaterResult[TRow] | None:
        """Update a single row by primary key."""
        return await execute_updater(self._sess, updater)

    async def batch_update[TRow: Base](self, updater: BatchUpdater[TRow]) -> BatchUpdaterResult:
        """Update all rows matching the updater conditions."""
        return await execute_batch_updater(self._sess, updater)

    async def bulk_update_partial[TRow: Base](
        self,
        updaters: list[Updater[TRow]],
    ) -> BulkUpdaterResult[TRow]:
        """Update multiple rows individually, isolating each via a savepoint for partial success."""
        return await execute_bulk_updater_partial(self._sess, updaters)

    async def upsert[TRow: Base](
        self,
        upserter: Upserter[TRow],
        index_elements: list[str],
    ) -> UpserterResult[TRow]:
        """Insert or update a single row on conflict."""
        return await execute_upserter(self._sess, upserter, index_elements=index_elements)

    async def purge[TRow: Base](self, purger: Purger[TRow]) -> PurgerResult[TRow] | None:
        """Delete a single row by primary key."""
        return await execute_purger(self._sess, purger)

    async def batch_purge[TRow: Base](self, purger: BatchPurger[TRow]) -> BatchPurgerResult:
        """Delete rows in batches matching the purger subquery."""
        return await execute_batch_purger(self._sess, purger)

    async def bulk_purge_partial[TRow: Base](
        self,
        purgers: list[Purger[TRow]],
    ) -> BulkPurgerResultWithFailures[TRow]:
        """Delete multiple rows individually, isolating each via a savepoint for partial success."""
        return await execute_bulk_purger_partial(self._sess, purgers)

    @asynccontextmanager
    async def savepoint(self) -> AsyncIterator[WriteOps]:
        """Open a nested transaction (savepoint) bound to the same session.

        A failure inside the block rolls back to the savepoint without aborting the
        enclosing transaction.
        """
        async with self._sess.begin_nested():
            yield WriteOps(self._sess)


class ScopeWriteOps:
    """Scope lifecycle write operations bound to a single session.

    Owns the scope provisioning / teardown orchestration that touches multiple
    RBAC tables (role presets, roles, permissions, association_scopes_entities,
    and the scope row itself). Generic single-table ops live on
    :class:`WriteOps`; this class is a sibling, not a subclass.
    """

    _sess: SASession

    def __init__(self, sess: SASession) -> None:
        self._sess = sess

    def _build_role_row_from_preset(self, preset: RolePresetRow) -> RoleRow:
        """Build a role row as a shallow snapshot of a role preset."""
        return RoleRow(name=preset.name)

    def _build_permission_row_from_preset(
        self,
        preset: RolePermissionPresetRow,
        scope_context: ScopeContext,
    ) -> PermissionRow:
        """Build a permission row from a role_permission_preset entry.

        ``role_id`` is left unset; the orchestrator back-fills it after the
        owning role row is flushed.
        """
        return PermissionRow(
            scope_type=scope_context.scope_type.to_scope_type(),
            scope_id=scope_context.scope_id,
            entity_type=preset.entity_type,
            operation=preset.operation,
        )

    async def _collect_role_entries_for_scope_type(
        self,
        scope_context: ScopeContext,
    ) -> list[_RoleEntry]:
        """Fetch active role presets matching the scope and build the role and
        permission rows snapshotted from each preset.

        One ``LEFT OUTER JOIN`` between ``role_presets`` and
        ``role_permission_presets`` is issued; the returned ``(preset,
        permission_preset_or_None)`` rows are grouped by preset id in Python.
        """
        rows = await self._sess.execute(
            sa.select(RolePresetRow, RolePermissionPresetRow)
            .select_from(RolePresetRow)
            .outerjoin(
                RolePermissionPresetRow,
                RolePermissionPresetRow.role_preset_id == RolePresetRow.id,
            )
            .where(
                RolePresetRow.scope_type == scope_context.scope_type.to_scope_type(),
                RolePresetRow.deleted.is_(False),
            )
        )

        entries_by_id: dict[RolePresetID, _RoleEntry] = {}
        for preset, permission_preset in rows:
            entry = entries_by_id.setdefault(
                preset.id,
                _RoleEntry(role=self._build_role_row_from_preset(preset), permissions=[]),
            )
            if permission_preset is not None:
                entry.permissions.append(
                    self._build_permission_row_from_preset(permission_preset, scope_context)
                )
        return list(entries_by_id.values())

    async def _create_preset_derived_roles_and_permissions(
        self,
        role_entries: list[_RoleEntry],
    ) -> list[RoleRow]:
        """Persist the pre-built role rows and their permission rows.

        Returned ``role_rows`` order matches ``role_entries``. Permission rows
        are inserted in the same transaction but are not returned.
        """
        if not role_entries:
            return []

        role_rows = [e.role for e in role_entries]
        self._sess.add_all(role_rows)
        await self._sess.flush()

        permission_rows: list[PermissionRow] = []
        for entry in role_entries:
            for permission in entry.permissions:
                permission.role_id = entry.role.id
                permission_rows.append(permission)
        if permission_rows:
            self._sess.add_all(permission_rows)
            await self._sess.flush()
        return role_rows

    async def _create_scope_associations(
        self,
        role_rows: list[RoleRow],
        parent_association_specs: Sequence[CreatorSpec[AssociationScopesEntitiesRow]],
        scope_context: ScopeContext,
    ) -> None:
        """Insert the scope's association_scopes_entities rows in one bulk call.

        Bundles two distinct kinds of mapping into a single insert: role-to-scope
        rows derived from ``role_rows`` and parent-scope mapping rows supplied
        by the scope creator spec.
        """
        role_scope_assoc_specs = [
            _RoleScopeAssociationSpec(role_id=r.id, scope_context=scope_context) for r in role_rows
        ]
        association_specs = role_scope_assoc_specs + list(parent_association_specs)
        if not association_specs:
            return
        await execute_bulk_creator(
            self._sess,
            BulkCreator(specs=association_specs),
        )

    async def create_scope[TScopeRow: Base](
        self,
        creator: ScopeCreator[TScopeRow],
    ) -> ScopeCreatorResult[TScopeRow]:
        """Provision a scope row together with its preset-derived roles and
        the scope's association rows.

        For every active role preset (``deleted = false``) matching the new
        scope's ``scope_type``, a role row, a role-to-scope association row,
        and one permission row per ``role_permission_presets`` entry are
        inserted in the same transaction as the scope row itself.
        """
        spec = creator.spec

        scope_res = await execute_creator(self._sess, Creator(spec=spec.scope_spec()))
        scope_context = spec.extract_scope_context(scope_res.row)

        role_entries = await self._collect_role_entries_for_scope_type(scope_context)
        role_rows = await self._create_preset_derived_roles_and_permissions(role_entries)
        await self._create_scope_associations(
            role_rows,
            spec.parent_association_specs(scope_res.row),
            scope_context,
        )

        return ScopeCreatorResult(scope_row=scope_res.row, role_rows=role_rows)

    async def purge_scope[TScopeRow: Base](
        self,
        purger: ScopePurger[TScopeRow],
    ) -> ScopePurgerResult[TScopeRow]:
        """Tear down a scope and the scope-bound RBAC rows it leaves behind.

        Order: scope-pinned permission rows, then association rows, then the scope
        row itself. Roles are not touched — role lifecycle is independent of scope
        lifecycle.
        """
        spec = purger.spec
        sess = self._sess
        scope_context = spec.scope_context()

        perm_res = await execute_batch_purger(
            sess,
            BatchPurger(spec=_ScopePermissionsPurgeSpec(scope_context=scope_context)),
        )

        assoc_res = await execute_batch_purger(
            sess,
            BatchPurger(spec=_ScopeAssociationsPurgeSpec(scope_context=scope_context)),
        )

        scope_res = await execute_purger(
            sess,
            Purger(row_class=spec.scope_row_class(), pk_value=spec.scope_pk_value()),
        )

        return ScopePurgerResult(
            scope_row=scope_res.row if scope_res is not None else None,
            deleted_permission_count=perm_res.deleted_count,
            deleted_association_count=assoc_res.deleted_count,
        )


class DBOpsProvider:
    """Entry point that isolates the engine and hands out session-bound ops.

    The engine is private; the only surface is ``read_ops()`` / ``write_ops()`` /
    ``scope_write_ops()``. All three use the READ COMMITTED isolation level.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @asynccontextmanager
    async def read_ops(self) -> AsyncIterator[ReadOps]:
        """Open a read-only transaction and yield read-only ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield ReadOps(sess)

    @asynccontextmanager
    async def write_ops(self) -> AsyncIterator[WriteOps]:
        """Open a read-write transaction and yield read-write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield WriteOps(sess)

    @asynccontextmanager
    async def scope_write_ops(self) -> AsyncIterator[ScopeWriteOps]:
        """Open a read-write transaction and yield the scope lifecycle writer ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield ScopeWriteOps(sess)
