"""RBAC-scoped DB ops: scope-associated entity creation and virtual-scope ownership
on top of the base write ops."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import AsyncIterator, Collection, Iterable, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.entity.types import EntityRef, ScopeRef
from ai.backend.common.data.permission.types import (
    Permission,
    RBACElementType,
    RelationType,
    ScopeType,
)
from ai.backend.common.exception import RBACTypeConversionError
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RBACElementRef,
    RoleSource,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as LegacyScopeType,
)
from ai.backend.manager.errors.permission import VirtualScopeNotFound
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.base import (
    BulkCreator,
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
    RBACEntityBatchPurger,
    RBACEntityBatchPurgerResult,
    RBACEntityPurger,
    RBACEntityPurgerResult,
    execute_rbac_entity_batch_purger,
    execute_rbac_entity_purger,
)
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider, WriteOps
from ai.backend.manager.repositories.permission_controller.creators import (
    PermissionCreatorSpec,
    RoleCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.role_manager import (
    RoleManager,
    ScopeSystemRoleData,
)


@dataclass(frozen=True)
class _RoleSpec:
    scope: ScopeRef
    creator: RoleCreatorSpec
    entity_operations: Mapping[RBACElementType, Iterable[OperationType]]


class ScopeCreation[TRow: Base](ABC):
    """A real scope-entity row to create, and how the RBAC layers address the result."""

    @abstractmethod
    def creator(self) -> RBACEntityCreator[TRow]:
        raise NotImplementedError

    @abstractmethod
    def scope_of(self, row: TRow) -> ScopeRef:
        raise NotImplementedError

    @abstractmethod
    def system_roles_of(self, row: TRow) -> Collection[ScopeSystemRoleData]:
        raise NotImplementedError


class ScopeMember(ABC):
    """A member to attach to a scope; ``assign_role_on`` names the user to grant its
    auto_assign roles, or ``None`` to skip."""

    @abstractmethod
    def entity_ref(self) -> EntityRef:
        raise NotImplementedError

    @abstractmethod
    def assign_role_on(self) -> UserID | None:
        raise NotImplementedError


@dataclass
class EntityMembersAddition:
    scope: ScopeRef
    members: Collection[ScopeMember]


@dataclass
class ScopeDeletion[TRow: Base]:
    """A real scope-entity row to delete together with its RBAC entries and virtual scope."""

    purger: RBACEntityPurger[TRow]
    scope: ScopeRef


@dataclass
class ScopeBatchDeletion[TRow: Base]:
    """A batch purger selecting real scope-entity rows to delete together with their RBAC
    entries, and the virtual scopes to drop for the deleted rows."""

    purger: RBACEntityBatchPurger[TRow]
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
        bound_scope: ScopeRef | None = None,
    ) -> RBACEntityCreatorResult[TRow]:
        """Create a scope in full: the real row with its parent scope association, its
        virtual scope node, its SYSTEM roles, and the roles from matching presets.

        The row is inserted first, so ``creation`` sees the id the database assigned. When
        ``bound_scope`` is given, it is bound to this scope's virtual scope so it can reach
        this scope's entities.
        """
        result = await self.create_scoped(creation.creator())
        scope = creation.scope_of(result.row)
        await self._insert_virtual_scopes([scope])
        if bound_scope is not None:
            await self.bind_scope(bound_scope, scope, permission_cap=None)
        await self._provision_scope_roles({scope: creation.system_roles_of(result.row)})
        return result

    async def bulk_create_scopes[TRow: Base](
        self,
        creations: Sequence[ScopeCreation[TRow]],
    ) -> RBACBulkEntityCreatorResult[TRow]:
        """Create multiple scopes in full, as :meth:`create_scope` does for one.

        The real scope rows are created atomically via a single bulk insert: either all
        rows and their scope associations are materialized, or the whole batch fails and
        nothing is created. The virtual scope inserts are idempotent (get-or-create).
        """
        result = await self.bulk_create_scoped([creation.creator() for creation in creations])
        scope_roles = {
            creation.scope_of(row): creation.system_roles_of(row)
            for creation, row in zip(creations, result.rows, strict=True)
        }
        await self._insert_virtual_scopes(list(scope_roles.keys()))
        await self._provision_scope_roles(scope_roles)
        return result

    # -- Scope lifecycle: roles provisioned with the scope ------------------------

    @staticmethod
    def _scope_element_type(scope: ScopeRef) -> RBACElementType:
        try:
            return RBACElementType(scope.scope_type)
        except ValueError as e:
            raise RBACTypeConversionError(
                f"Scope type {scope.scope_type!r} has no corresponding RBAC element type"
            ) from e

    @staticmethod
    def _system_role_specs(
        scope_roles: Mapping[ScopeRef, Collection[ScopeSystemRoleData]],
    ) -> list[_RoleSpec]:
        return [
            _RoleSpec(
                scope=scope,
                creator=RoleCreatorSpec(
                    name=role_data.role_name(),
                    source=RoleSource.SYSTEM,
                    status=RoleStatus.ACTIVE,
                ),
                entity_operations=role_data.entity_operations(),
            )
            for scope, role_datas in scope_roles.items()
            for role_data in role_datas
        ]

    async def _provision_scope_roles(
        self,
        scope_roles: Mapping[ScopeRef, Collection[ScopeSystemRoleData]],
    ) -> None:
        """Create every scope's declared SYSTEM roles and its preset-derived roles.

        Whatever the number of scopes and roles, this issues one insert for all the roles
        and one for all their permissions.
        """
        role_specs = self._system_role_specs(scope_roles)
        preset_role_specs = await self._preset_role_specs(scope_roles.keys())
        specs = [*role_specs, *preset_role_specs]
        if not specs:
            return
        await self._create_roles(specs)

    async def _preset_role_specs(self, scopes: Collection[ScopeRef]) -> list[_RoleSpec]:
        """The roles the active presets matching ``scopes``' types call for."""
        if not scopes:
            return []
        preset_rows = (
            await self._sess.scalars(
                sa.select(RolePresetRow).where(
                    RolePresetRow.scope_type.in_({
                        self._scope_element_type(scope).to_scope_type() for scope in scopes
                    }),
                    RolePresetRow.deleted.is_(False),
                )
            )
        ).all()
        if not preset_rows:
            return []
        operations_by_preset: dict[RolePresetID, dict[RBACElementType, list[OperationType]]] = (
            defaultdict(lambda: defaultdict(list))
        )
        preset_permission_rows = (
            await self._sess.scalars(
                sa.select(RolePermissionPresetRow).where(
                    RolePermissionPresetRow.role_preset_id.in_([
                        preset.id for preset in preset_rows
                    ])
                )
            )
        ).all()
        for preset_permission in preset_permission_rows:
            operations_by_preset[preset_permission.role_preset_id][
                preset_permission.entity_type.to_element()
            ].append(preset_permission.operation)
        presets_by_scope_type: dict[ScopeType, list[RolePresetRow]] = defaultdict(list)
        for preset in preset_rows:
            presets_by_scope_type[preset.scope_type].append(preset)
        return [
            _RoleSpec(
                scope=scope,
                creator=RoleCreatorSpec(
                    name=preset.name,
                    source=RoleSource.SYSTEM,
                    status=RoleStatus.ACTIVE,
                    auto_assign=preset.auto_assign,
                ),
                entity_operations=operations_by_preset[preset.id],
            )
            for scope in scopes
            for preset in presets_by_scope_type[self._scope_element_type(scope).to_scope_type()]
        ]

    async def _create_roles(self, specs: Sequence[_RoleSpec]) -> None:
        """Create ``specs`` and the permissions they grant: one insert for each."""
        if not specs:
            return
        roles = await self.bulk_create_scoped([
            RBACEntityCreator(
                spec=spec.creator,
                element_type=RBACElementType.ROLE,
                scope_ref=RBACElementRef(
                    element_type=self._scope_element_type(spec.scope),
                    element_id=str(spec.scope.scope_id),
                ),
            )
            for spec in specs
        ])
        permissions = [
            PermissionCreatorSpec(
                role_id=row.id,
                scope_type=self._scope_element_type(spec.scope),
                scope_id=str(spec.scope.scope_id),
                entity_type=entity_type,
                operation=operation,
            )
            for spec, row in zip(specs, roles.rows, strict=True)
            for entity_type, operations in spec.entity_operations.items()
            for operation in operations
        ]
        if permissions:
            await self.bulk_create(BulkCreator(specs=permissions))

    async def delete_scope[TRow: Base](
        self,
        deletion: ScopeDeletion[TRow],
    ) -> RBACEntityPurgerResult[TRow] | None:
        """Delete a scope in full: the real row with its RBAC entries (permissions and
        scope associations in both directions) and its virtual scope node.

        Deleting the virtual scope cascades to its scope bindings and entity
        memberships (FK ``ON DELETE CASCADE``). Returns ``None`` if the row is
        already gone.
        """
        result = await self.purge_scoped(deletion.purger)
        await self._delete_virtual_scopes([deletion.scope])
        return result

    async def batch_delete_scopes[TRow: Base](
        self,
        deletion: ScopeBatchDeletion[TRow],
    ) -> RBACEntityBatchPurgerResult:
        """Delete the scopes matched by ``deletion.purger`` in full, as
        :meth:`delete_scope` does for one.

        The real scope rows are purged in batches with their RBAC entries, then the
        virtual scope nodes for ``deletion.scopes`` are dropped (FK ``ON DELETE CASCADE``
        removes their edges).
        """
        result = await execute_rbac_entity_batch_purger(self._sess, deletion.purger)
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
        addition: EntityMembersAddition,
    ) -> None:
        """Write each member's virtual-scope membership and scope association, and grant the
        scope's auto_assign roles to members whose ``assign_role_on`` returns a user id."""
        members = list(addition.members)
        if not members:
            return
        scope = addition.scope
        virtual_scope_id = await self._resolve_virtual_scope_id(scope)
        entity_refs = [member.entity_ref() for member in members]
        membership_values = [
            {
                "virtual_scope_id": virtual_scope_id,
                "entity_type": ref.entity_type,
                "entity_id": ref.entity_id,
                "permission_cap": None,
            }
            for ref in entity_refs
        ]
        await self._sess.execute(
            pg_insert(EntityMembershipRow).values(membership_values).on_conflict_do_nothing()
        )
        association_values = [
            {
                "scope_type": LegacyScopeType(scope.scope_type),
                "scope_id": str(scope.scope_id),
                "entity_type": EntityType(ref.entity_type),
                "entity_id": str(ref.entity_id),
                "relation_type": RelationType.AUTO,
                "permission_cap": None,
            }
            for ref in entity_refs
        ]
        await self._sess.execute(
            pg_insert(AssociationScopesEntitiesRow)
            .values(association_values)
            .on_conflict_do_nothing()
        )
        role_user_ids = [
            user_id for member in members if (user_id := member.assign_role_on()) is not None
        ]
        if role_user_ids:
            await self._role_manager.assign_auto_assign_roles(
                self._sess,
                role_user_ids,
                ScopeId(
                    scope_type=LegacyScopeType(scope.scope_type),
                    scope_id=str(scope.scope_id),
                ),
            )

    async def remove_entity_members(
        self,
        scope: ScopeRef,
        entities: Collection[EntityRef],
    ) -> None:
        """Delete each entity's virtual-scope membership and scope association; role mappings
        are left untouched."""
        entity_refs = list(entities)
        if not entity_refs:
            return
        virtual_scope_id = await self._resolve_virtual_scope_id(scope)
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_scope_id == virtual_scope_id,
                sa.tuple_(EntityMembershipRow.entity_type, EntityMembershipRow.entity_id).in_([
                    (ref.entity_type, ref.entity_id) for ref in entity_refs
                ]),
            )
        )
        await self._sess.execute(
            sa.delete(AssociationScopesEntitiesRow).where(
                AssociationScopesEntitiesRow.scope_type == LegacyScopeType(scope.scope_type),
                AssociationScopesEntitiesRow.scope_id == str(scope.scope_id),
                sa.tuple_(
                    AssociationScopesEntitiesRow.entity_type,
                    AssociationScopesEntitiesRow.entity_id,
                ).in_([(EntityType(ref.entity_type), str(ref.entity_id)) for ref in entity_refs]),
            )
        )

    # -- Virtual scope: ensure compatibility for externally-created rows ----------

    async def ensure_scope(
        self,
        scope: ScopeRef,
        bound_scope: ScopeRef | None = None,
    ) -> None:
        """Ensure the virtual scope node for an already-created ``scope``. When ``bound_scope``
        is given, it is bound to this scope's virtual scope. Idempotent.
        """
        await self._insert_virtual_scopes([scope])
        if bound_scope is not None:
            await self.bind_scope(bound_scope, scope, permission_cap=None)


class RBACOpsProvider(DBOpsProvider):
    """Hands out :class:`RBACWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncIterator[RBACWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield RBACWriteOps(sess)
