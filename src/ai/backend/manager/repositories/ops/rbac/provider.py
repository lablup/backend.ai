"""RBAC-scoped DB ops: scope-associated entity creation and virtual-scope ownership
on top of the base write ops."""

from __future__ import annotations

from collections.abc import AsyncIterator, Collection, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.entity.types import EntityRef, ScopeRef
from ai.backend.common.data.permission.types import Permission, RelationType
from ai.backend.common.identifier.user import UserID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.errors.permission import VirtualScopeNotFound
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchPurgerResult,
    BulkCreator,
    BulkCreatorResult,
    Creator,
    CreatorResult,
    Purger,
    PurgerResult,
)
from ai.backend.manager.repositories.base.creator import BulkCreatorError
from ai.backend.manager.repositories.base.integrity import parse_integrity_error
from ai.backend.manager.repositories.base.purger import (
    BulkPurgerError,
    BulkPurgerResultWithFailures,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACBulkEntityCreatorResult,
    RBACBulkEntityCreatorResultWithFailures,
    RBACEntityCreator,
    RBACEntityCreatorResult,
    execute_rbac_entity_creator,
    execute_rbac_entity_creators,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntityPurger,
    RBACEntityPurgerResult,
    execute_rbac_entity_purger,
)
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider, WriteOps
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager


@dataclass
class ScopeCreation[TRow: Base]:
    """A real scope-entity row to create together with the scope it materializes.

    ``scope.scope_id`` must be the id the created row will carry.
    """

    creator: Creator[TRow]
    scope: ScopeRef


@dataclass
class ScopeDeletion[TRow: Base]:
    """A real scope-entity row to delete together with its virtual scope."""

    purger: Purger[TRow]
    scope: ScopeRef


@dataclass
class ScopeBatchDeletion[TRow: Base]:
    """A batch purger selecting real scope-entity rows to delete, together with the
    virtual scopes to drop for the deleted rows."""

    purger: BatchPurger[TRow]
    scopes: Sequence[ScopeRef]


class RBACWriteOps(WriteOps):
    """Base write ops plus RBAC scope-associated creation and virtual-scope writes."""

    _role_manager: RoleManager

    def __init__(self, sess: SASession) -> None:
        super().__init__(sess)
        self._role_manager = RoleManager()

    # -- Virtual-scope helpers ----------------------------------------------------

    async def _resolve_virtual_scope_id(self, scope: ScopeRef) -> VirtualScopeID:
        """Return the virtual scope id backing ``scope``.

        Every owner scope is created with its virtual scope, so a missing one is an
        invariant violation: raises :class:`VirtualScopeNotFound` (500).
        """
        stmt = sa.select(VirtualScopeRow.id).where(
            VirtualScopeRow.scope_type == scope.scope_type,
            VirtualScopeRow.scope_id == scope.scope_id,
        )
        virtual_scope_id = (await self._sess.execute(stmt)).scalar_one_or_none()
        if virtual_scope_id is None:
            raise VirtualScopeNotFound(
                f"No virtual scope for scope {scope.scope_type}:{scope.scope_id}"
            )
        return virtual_scope_id

    async def _insert_virtual_scopes(self, scopes: Sequence[ScopeRef]) -> None:
        """Create each scope's virtual scope node with its self entity-membership and self
        scope_binding (permission_cap NULL). Idempotent: an existing scope is a no-op."""
        if not scopes:
            return
        values = [{"scope_type": s.scope_type, "scope_id": s.scope_id} for s in scopes]
        insert_stmt = (
            pg_insert(VirtualScopeRow)
            .values(values)
            .on_conflict_do_nothing(index_elements=["scope_type", "scope_id"])
            .returning(
                VirtualScopeRow.id,
                VirtualScopeRow.scope_type,
                VirtualScopeRow.scope_id,
            )
        )
        inserted = (await self._sess.execute(insert_stmt)).all()
        if not inserted:
            return
        membership_stmt = (
            pg_insert(EntityMembershipRow)
            .values([
                {
                    "virtual_scope_id": row.id,
                    "entity_type": row.scope_type,
                    "entity_id": row.scope_id,
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
                    "virtual_scope_id": row.id,
                    "scope_type": row.scope_type,
                    "scope_id": row.scope_id,
                    "permission_cap": None,
                }
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(binding_stmt)

    async def _delete_virtual_scopes(self, scopes: Sequence[ScopeRef]) -> None:
        """Delete the virtual scope nodes for ``scopes`` (FK CASCADE removes their edges)."""
        if not scopes:
            return
        stmt = sa.delete(VirtualScopeRow).where(
            sa.tuple_(VirtualScopeRow.scope_type, VirtualScopeRow.scope_id).in_([
                (s.scope_type, s.scope_id) for s in scopes
            ])
        )
        await self._sess.execute(stmt)

    async def create_scoped[TRow: Base](
        self,
        creator: RBACEntityCreator[TRow],
    ) -> RBACEntityCreatorResult[TRow]:
        """Insert one row with its RBAC scope association (the creator carries its scope)."""
        return await execute_rbac_entity_creator(self._sess, creator)

    async def bulk_create_scoped[TRow: Base](
        self,
        creators: Sequence[RBACEntityCreator[TRow]],
    ) -> RBACBulkEntityCreatorResult[TRow]:
        """Insert rows with their RBAC scope associations (each creator carries its scope)."""
        return await execute_rbac_entity_creators(self._sess, creators)

    async def bulk_create_scoped_partial[TRow: Base](
        self,
        creators: Sequence[RBACEntityCreator[TRow]],
    ) -> RBACBulkEntityCreatorResultWithFailures[TRow]:
        """Insert rows with their scope associations, isolating each row for partial success.

        The scoped counterpart of :meth:`bulk_create_partial`: a row and its association share
        one savepoint, so a rejected row rolls back both and leaves the rest created.
        :meth:`bulk_create_scoped` flushes the batch at once instead and is all-or-nothing.
        """
        successes: list[TRow] = []
        errors: list[BulkCreatorError[TRow]] = []
        for index, creator in enumerate(creators):
            # The handlers stay outside the savepoint: a failure has to reach the context
            # manager for it to roll back. Catching inside would leave it releasing a
            # savepoint the failed statement already aborted, which kills the whole batch.
            try:
                async with self.savepoint():
                    result = await execute_rbac_entity_creator(self._sess, creator)
                successes.append(result.row)
            except sa.exc.IntegrityError as e:
                errors.append(
                    BulkCreatorError(
                        spec=creator.spec, exception=parse_integrity_error(e), index=index
                    )
                )
            except Exception as e:
                # execute_rbac_entity_creator maps the integrity errors its spec declares
                # onto domain errors; whatever arrives here fails just this row.
                errors.append(BulkCreatorError(spec=creator.spec, exception=e, index=index))
        return RBACBulkEntityCreatorResultWithFailures(successes=successes, errors=errors)

    async def purge_scoped[TRow: Base](
        self,
        purger: RBACEntityPurger[TRow],
    ) -> RBACEntityPurgerResult[TRow] | None:
        """Delete one row and its RBAC entries; ``None`` if the row is already gone."""
        return await execute_rbac_entity_purger(self._sess, purger)

    async def bulk_purge_scoped_partial[TRow: Base](
        self,
        purgers: Sequence[RBACEntityPurger[TRow]],
    ) -> BulkPurgerResultWithFailures[TRow]:
        """Delete rows with their RBAC entries, isolating each row for partial success.

        The scoped counterpart of :meth:`bulk_purge_partial`: a row and its RBAC entries share
        one savepoint, so a failed row rolls back both and leaves the rest deleted. A purger
        targeting a row that is already gone is skipped — no success, no error.
        """
        successes: list[TRow] = []
        errors: list[BulkPurgerError[TRow]] = []
        for index, purger in enumerate(purgers):
            # The handler stays outside the savepoint — see bulk_create_scoped_partial.
            try:
                async with self.savepoint():
                    result = await execute_rbac_entity_purger(self._sess, purger)
                if result is not None:
                    successes.append(result.row)
            except Exception as e:
                errors.append(BulkPurgerError(purger=purger, exception=e, index=index))
        return BulkPurgerResultWithFailures(successes=successes, errors=errors)

    async def add_users_to_scope(
        self,
        scope_id: ScopeId,
        user_ids: Collection[UserID],
    ) -> None:
        """Bind users to a scope and grant the scope's ``auto_assign`` roles.

        Inserts the user-scope associations (``association_scopes_entities``,
        ON CONFLICT DO NOTHING) and maps every user to each active
        ``auto_assign`` role bound to the scope. Idempotent: re-binding an
        existing membership is a no-op and already-granted roles are skipped,
        so it is safe to call even when the scope association already exists.
        """
        if not user_ids:
            return
        values = [
            {
                "scope_type": scope_id.scope_type,
                "scope_id": scope_id.scope_id,
                "entity_type": EntityType.USER,
                "entity_id": str(user_id),
                "relation_type": RelationType.AUTO,
                "permission_cap": None,
            }
            for user_id in user_ids
        ]
        stmt = pg_insert(AssociationScopesEntitiesRow).values(values).on_conflict_do_nothing()
        await self._sess.execute(stmt)
        await self._role_manager.assign_auto_assign_roles(self._sess, user_ids, scope_id)

    # -- Scope lifecycle: real scope entity + its virtual scope node --------------

    async def create_scope[TRow: Base](
        self,
        creation: ScopeCreation[TRow],
        parent: ScopeRef | None = None,
    ) -> CreatorResult[TRow]:
        """Create the real scope entity via ``creation.creator`` and its virtual scope node.

        ``creation.scope.scope_id`` must match the id the created row carries. When ``parent``
        is given, the parent scope is bound to this scope's virtual scope so it can reach this
        scope's entities.
        """
        result = await self.create(creation.creator)
        await self._insert_virtual_scopes([creation.scope])
        if parent is not None:
            await self.bind_scope(parent, creation.scope, permission_cap=None)
        return result

    async def bulk_create_scopes[TRow: Base](
        self,
        creations: Sequence[ScopeCreation[TRow]],
    ) -> BulkCreatorResult[TRow]:
        """Create multiple real scope entities and their virtual scope nodes.

        The real scope rows are created atomically via a single bulk insert: either all
        rows and their virtual scope nodes are materialized, or the whole batch fails and
        nothing is created. The virtual scope inserts are idempotent (get-or-create).
        """
        result = await self.bulk_create(
            BulkCreator(specs=[creation.creator.spec for creation in creations]),
        )
        await self._insert_virtual_scopes([creation.scope for creation in creations])
        return result

    async def delete_scope[TRow: Base](
        self,
        deletion: ScopeDeletion[TRow],
    ) -> PurgerResult[TRow] | None:
        """Delete the real scope entity via ``deletion.purger`` and its virtual scope node.

        Deleting the virtual scope cascades to its scope bindings and entity
        memberships (FK ``ON DELETE CASCADE``).
        """
        result = await self.purge(deletion.purger)
        await self._delete_virtual_scopes([deletion.scope])
        return result

    async def batch_delete_scopes[TRow: Base](
        self,
        deletion: ScopeBatchDeletion[TRow],
    ) -> BatchPurgerResult:
        """Delete the real scope entities matched by ``deletion.purger`` and their virtual
        scope nodes.

        The real scope rows are purged atomically via the batch purge (all-or-nothing), then
        the virtual scope nodes for ``deletion.scopes`` are dropped (FK ``ON DELETE CASCADE``
        removes their edges).
        """
        result = await self.batch_purge(deletion.purger)
        await self._delete_virtual_scopes(deletion.scopes)
        return result

    # -- Virtual scope: inbound edges (scope_bindings) ----------------------------

    async def bind_scope(
        self,
        scope: ScopeRef,
        owner: ScopeRef,
        permission_cap: Permission | None,
    ) -> None:
        """Bind ``scope`` to ``owner``'s virtual scope so it reaches ``owner``'s entities.

        Resolves ``owner``'s virtual scope (raises :class:`VirtualScopeNotFound` if
        absent). Idempotent: ON CONFLICT DO NOTHING on the binding's primary key —
        an existing binding keeps its ``permission_cap``.
        """
        virtual_scope_id = await self._resolve_virtual_scope_id(owner)
        stmt = (
            pg_insert(ScopeBindingRow)
            .values(
                virtual_scope_id=virtual_scope_id,
                scope_type=scope.scope_type,
                scope_id=scope.scope_id,
                permission_cap=permission_cap,
            )
            .on_conflict_do_nothing()
        )
        await self._sess.execute(stmt)

    async def unbind_scope(self, scope: ScopeRef, owner: ScopeRef) -> None:
        """Remove ``scope``'s binding to ``owner``'s virtual scope."""
        virtual_scope_id = await self._resolve_virtual_scope_id(owner)
        stmt = sa.delete(ScopeBindingRow).where(
            ScopeBindingRow.virtual_scope_id == virtual_scope_id,
            ScopeBindingRow.scope_type == scope.scope_type,
            ScopeBindingRow.scope_id == scope.scope_id,
        )
        await self._sess.execute(stmt)

    # -- Virtual scope: outbound edges (entity_memberships) -----------------------

    async def add_entity_members(
        self,
        scope: ScopeRef,
        entities: Collection[EntityRef],
        permission_cap: Permission | None,
    ) -> None:
        """Attach ``entities`` (possibly of mixed types) to ``scope``'s virtual scope.

        Resolves ``scope``'s virtual scope (raises :class:`VirtualScopeNotFound` if
        absent). Idempotent: ON CONFLICT DO NOTHING on the membership's primary key.
        """
        if not entities:
            return
        virtual_scope_id = await self._resolve_virtual_scope_id(scope)
        values = [
            {
                "virtual_scope_id": virtual_scope_id,
                "entity_type": entity.entity_type,
                "entity_id": entity.entity_id,
                "permission_cap": permission_cap,
            }
            for entity in entities
        ]
        stmt = pg_insert(EntityMembershipRow).values(values).on_conflict_do_nothing()
        await self._sess.execute(stmt)

    async def remove_entity_members(
        self,
        scope: ScopeRef,
        entities: Collection[EntityRef],
    ) -> None:
        """Detach ``entities`` from ``scope``'s virtual scope."""
        if not entities:
            return
        virtual_scope_id = await self._resolve_virtual_scope_id(scope)
        stmt = sa.delete(EntityMembershipRow).where(
            EntityMembershipRow.virtual_scope_id == virtual_scope_id,
            sa.tuple_(EntityMembershipRow.entity_type, EntityMembershipRow.entity_id).in_([
                (entity.entity_type, entity.entity_id) for entity in entities
            ]),
        )
        await self._sess.execute(stmt)

    # -- Virtual scope: ensure compatibility for externally-created rows ----------

    async def ensure_scope(
        self,
        scope: ScopeRef,
        parent: ScopeRef | None = None,
    ) -> None:
        """Ensure the virtual scope node for an already-created ``scope``. When ``parent`` is
        given, the parent scope is bound to this scope's virtual scope. Idempotent.
        """
        await self._insert_virtual_scopes([scope])
        if parent is not None:
            await self.bind_scope(parent, scope, permission_cap=None)


class RBACOpsProvider(DBOpsProvider):
    """Hands out :class:`RBACWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncIterator[RBACWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield RBACWriteOps(sess)
