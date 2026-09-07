"""RBAC-scoped DB ops: scope-associated entity creation and virtual-entity ownership
on top of the base write ops."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Collection, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.types import EntityRef, ScopeRef, ScopeType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import (
    Permission,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType as LegacyEntityType,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as LegacyScopeType,
)
from ai.backend.manager.errors.permission import VirtualEntityNotFound
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base import (
    BulkCreator,
    CreatorSpec,
    DependentCreatorSpec,
)
from ai.backend.manager.repositories.base.rbac.utils import bulk_insert_on_conflict_do_nothing
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider, WriteOps
from ai.backend.manager.repositories.permission_controller.creators import (
    AssociationScopesEntitiesCreatorSpec,
    ScopeBindingCreatorSpec,
    UserRoleCreatorSpec,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScopeMember(ABC):
    """A member to attach to a scope; ``assign_role_on`` names the user to grant its
    auto_assign roles, or ``None`` to skip, and ``permission_cap`` gives the cap every
    row of this member kind carries in that scope kind."""

    @abstractmethod
    def entity_ref(self) -> EntityRef:
        raise NotImplementedError

    @abstractmethod
    def assign_role_on(self) -> UserID | None:
        raise NotImplementedError

    @abstractmethod
    def permission_cap(self, scope: ScopeRef) -> Permission | None:
        raise NotImplementedError


@dataclass
class ScopeUserMember(ScopeMember):
    """A user joining a scope; membership always grants the scope's ``auto_assign``
    roles (idempotently), so membership and role state cannot drift apart."""

    user_id: UserID

    @override
    def entity_ref(self) -> EntityRef:
        return EntityRef(entity_type=USER_ENTITY_TYPE, entity_id=self.user_id)

    @override
    def assign_role_on(self) -> UserID:
        return self.user_id

    @override
    def permission_cap(self, scope: ScopeRef) -> Permission | None:
        """A project roster caps its users to read; a domain roster carries no cap."""
        if scope.scope_type == PROJECT_SCOPE_TYPE:
            return Permission.READ
        return None


@dataclass
class ScopeEntityMember(ScopeMember):
    """A non-user entity joining a scope; no roles are granted for it."""

    ref: EntityRef

    @override
    def entity_ref(self) -> EntityRef:
        return self.ref

    @override
    def assign_role_on(self) -> UserID | None:
        return None

    @override
    def permission_cap(self, scope: ScopeRef) -> Permission | None:
        return None


@dataclass
class EntityMembersAddition:
    scope: ScopeRef
    members: Collection[ScopeMember]


@dataclass
class EntityMemberCreationError:
    """A member whose addition failed, with the exception that rolled it back."""

    member: ScopeMember
    exception: Exception
    index: int


@dataclass
class EntityMembersResultWithFailures:
    successes: list[ScopeMember]
    errors: list[EntityMemberCreationError]


class RBACWriteOps(WriteOps):
    """Base write ops plus RBAC scope-associated creation and virtual-entity writes."""

    async def _bulk_create_ignore_conflicts[TRow: Base](
        self, specs: Sequence[CreatorSpec[TRow]]
    ) -> None:
        """Insert rows from ``specs`` in one statement, skipping rows that conflict
        with existing ones (``ON CONFLICT DO NOTHING``); existing rows are kept as-is."""
        await bulk_insert_on_conflict_do_nothing(self._sess, [spec.build_row() for spec in specs])

    async def _bulk_create_dependent_ignore_conflicts[TDependency, TRow: Base](
        self,
        specs: Sequence[DependentCreatorSpec[TDependency, TRow]],
        dependency: TDependency,
    ) -> None:
        """Insert dependency-resolved rows from ``specs``, skipping rows that conflict
        with existing ones (``ON CONFLICT DO NOTHING``); existing rows are kept as-is."""
        await bulk_insert_on_conflict_do_nothing(
            self._sess, [spec.build_row(dependency) for spec in specs]
        )

    # -- Virtual-entity helpers ----------------------------------------------------

    async def _find_virtual_entity_id(self, scope: ScopeRef) -> VirtualEntityID | None:
        """Return the virtual entity id backing ``scope``, or ``None`` if it has none."""
        stmt = sa.select(VirtualEntityRow.id).where(
            VirtualEntityRow.entity_type == scope.scope_type,
            VirtualEntityRow.entity_id == scope.scope_id,
        )
        return (await self._sess.execute(stmt)).scalar_one_or_none()

    async def _resolve_virtual_entity_id(self, scope: ScopeRef) -> VirtualEntityID:
        """Return the virtual entity id backing ``scope``.

        Every owner scope is created with its virtual entity, so a missing one is an
        invariant violation: raises :class:`VirtualEntityNotFound` (500).
        """
        virtual_entity_id = await self._find_virtual_entity_id(scope)
        if virtual_entity_id is None:
            raise VirtualEntityNotFound(
                f"No virtual entity for scope {scope.scope_type}:{scope.scope_id}"
            )
        return virtual_entity_id

    async def _find_virtual_entity_ids(
        self, scopes: Sequence[ScopeRef]
    ) -> dict[ScopeRef, VirtualEntityID]:
        """Return the virtual entity ids backing ``scopes`` in one query; scopes
        without one are absent from the result."""
        if not scopes:
            return {}
        stmt = sa.select(
            VirtualEntityRow.entity_type,
            VirtualEntityRow.entity_id,
            VirtualEntityRow.id,
        ).where(
            sa.tuple_(VirtualEntityRow.entity_type, VirtualEntityRow.entity_id).in_([
                (s.scope_type, s.scope_id) for s in scopes
            ])
        )
        return {
            ScopeRef(scope_type=ScopeType(row.entity_type), scope_id=row.entity_id): row.id
            for row in (await self._sess.execute(stmt)).all()
        }

    async def _resolve_virtual_entity_ids(
        self, scopes: Sequence[ScopeRef]
    ) -> dict[ScopeRef, VirtualEntityID]:
        """Return the virtual entity id backing each of ``scopes`` in one query.

        As with :meth:`_resolve_virtual_entity_id`, a scope without a virtual entity is
        an invariant violation: raises :class:`VirtualEntityNotFound` naming them all.
        """
        resolved = await self._find_virtual_entity_ids(scopes)
        missing = [s for s in scopes if s not in resolved]
        if missing:
            raise VirtualEntityNotFound(
                "No virtual entity for scopes: "
                + ", ".join(f"{s.scope_type}:{s.scope_id}" for s in missing)
            )
        return resolved

    async def _insert_virtual_entities(self, scopes: Sequence[ScopeRef]) -> None:
        """Create each scope's virtual entity node with its self entity-membership and self
        scope_binding (permission_cap NULL). Idempotent: an existing scope is a no-op."""
        if not scopes:
            return
        values = [{"entity_type": s.scope_type, "entity_id": s.scope_id} for s in scopes]
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
                    "capped": False,
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

    async def _grant_auto_assign_roles(
        self,
        scope_id: ScopeId,
        user_ids: Collection[UserID],
    ) -> None:
        """Map users to every active ``auto_assign`` role bound to ``scope_id``.

        Roles bound to the scope are located via the scope-entity association
        (``association_scopes_entities`` with ``entity_type == ROLE``); already-granted
        pairs are skipped.
        """
        unique_user_ids = set(user_ids)
        if not unique_user_ids:
            return
        # One query: the scope's auto_assign roles, outer-joined with the target
        # users' existing grants (user_id is NULL for roles no target user holds).
        rows = (
            await self._sess.execute(
                sa.select(RoleRow.id.label("role_id"), UserRoleRow.user_id.label("user_id"))
                .join(
                    AssociationScopesEntitiesRow,
                    sa.cast(AssociationScopesEntitiesRow.entity_id, sa.String)
                    == sa.cast(RoleRow.id, sa.String),
                )
                .outerjoin(
                    UserRoleRow,
                    sa.and_(
                        UserRoleRow.role_id == RoleRow.id,
                        UserRoleRow.user_id.in_(unique_user_ids),
                    ),
                )
                .where(
                    AssociationScopesEntitiesRow.scope_type == scope_id.scope_type,
                    AssociationScopesEntitiesRow.scope_id == scope_id.scope_id,
                    AssociationScopesEntitiesRow.entity_type == LegacyEntityType.ROLE,
                    RoleRow.auto_assign.is_(True),
                    RoleRow.status == RoleStatus.ACTIVE,
                )
            )
        ).all()
        role_ids = {row.role_id for row in rows}
        existing_pairs = {(row.user_id, row.role_id) for row in rows if row.user_id is not None}
        specs = [
            UserRoleCreatorSpec(user_id=user_id, role_id=role_id)
            for user_id in unique_user_ids
            for role_id in role_ids
            if (user_id, role_id) not in existing_pairs
        ]
        if specs:
            await self.bulk_create(BulkCreator(specs=specs))

    async def assign_roles_to_user(
        self,
        user_id: UserID,
        role_ids: Collection[UUID],
    ) -> None:
        """Map ``user_id`` to each of ``role_ids``; already-granted pairs are skipped."""
        if not role_ids:
            return
        existing_role_ids = set(
            (
                await self._sess.scalars(
                    sa.select(UserRoleRow.role_id).where(
                        UserRoleRow.user_id == user_id,
                        UserRoleRow.role_id.in_(role_ids),
                    )
                )
            ).all()
        )
        specs = [
            UserRoleCreatorSpec(user_id=user_id, role_id=role_id)
            for role_id in role_ids
            if role_id not in existing_role_ids
        ]
        if specs:
            await self.bulk_create(BulkCreator(specs=specs))

    async def add_bulk_members(
        self,
        addition: EntityMembersAddition,
    ) -> None:
        """Attach each member under the scope: membership in the scope's virtual entity,
        carrying the member kind's constant cap, and the legacy scope association. The
        scope reaches the member entities themselves, not the entities they own — use
        :meth:`add_bulk_inheriting_members` when the member must inherit the scope's
        permissions over what it owns. Grants the scope's auto_assign roles to members
        whose ``assign_role_on`` returns a user id.

        Raises :class:`VirtualEntityNotFound` if the scope has no virtual entity.
        Idempotent: existing rows keep their cap.
        """
        members = list(addition.members)
        if not members:
            return
        scope = addition.scope
        virtual_entity_id = await self._resolve_virtual_entity_id(scope)
        await self._enroll_members_in_scope_ve(virtual_entity_id, scope, members)
        await self._associate_entities_with_scope(
            scope, [member.entity_ref() for member in members]
        )
        await self._grant_member_auto_assign_roles(scope, members)

    async def add_bulk_inheriting_members(
        self,
        addition: EntityMembersAddition,
    ) -> None:
        """Attach each member so that it inherits the scope's permissions: everything
        :meth:`add_bulk_members` writes, plus the binding that carries those permissions
        onto every entity the member owns.

        Only for relations where that inheritance is intended — a domain over its
        projects, a project over the container registries it contains. Joining a scope's
        roster is not such a relation: a user is an ordinary member of both its domain
        and its projects, and no row ever binds a user's virtual entity into a scope.
        Inheritance stays unidirectional; the reverse would widen every member-scoped
        role at once.

        Raises :class:`VirtualEntityNotFound` for any missing virtual entity. Idempotent:
        existing rows keep their cap.
        """
        members = list(addition.members)
        if not members:
            return
        await self.add_bulk_members(addition)
        member_scopes = [self._member_scope_ref(member.entity_ref()) for member in members]
        await self._bind_scope_to_member_vs(addition.scope, member_scopes)

    async def add_bulk_members_partial(
        self,
        addition: EntityMembersAddition,
    ) -> EntityMembersResultWithFailures:
        """Add members as :meth:`add_bulk_members` does, isolating each member in its
        own savepoint: a failed member — including one without a virtual entity — lands
        in ``errors`` while the rest are added. Roles are granted only to the
        successful members.
        """
        successes: list[ScopeMember] = []
        errors: list[EntityMemberCreationError] = []
        members = list(addition.members)
        if not members:
            return EntityMembersResultWithFailures(successes=successes, errors=errors)
        scope = addition.scope
        virtual_entity_id = await self._resolve_virtual_entity_id(scope)
        for index, member in enumerate(members):
            # The handler stays outside the savepoint — see bulk_create_scoped_partial.
            try:
                async with self.savepoint():
                    await self._enroll_members_in_scope_ve(virtual_entity_id, scope, [member])
                    await self._associate_entities_with_scope(scope, [member.entity_ref()])
                successes.append(member)
            except Exception as e:
                errors.append(EntityMemberCreationError(member=member, exception=e, index=index))
        await self._grant_member_auto_assign_roles(scope, successes)
        return EntityMembersResultWithFailures(successes=successes, errors=errors)

    async def _enroll_members_in_scope_ve(
        self,
        virtual_entity_id: VirtualEntityID,
        scope: ScopeRef,
        members: Sequence[ScopeMember],
    ) -> None:
        """Enroll each member in the scope's virtual entity with its kind's cap; raises
        :class:`VirtualEntityNotFound` for members without a virtual entity."""
        member_scopes = [self._member_scope_ref(member.entity_ref()) for member in members]
        member_virtual_entity_ids = await self._resolve_virtual_entity_ids(member_scopes)
        caps = {
            member_virtual_entity_ids[member_scope]: member.permission_cap(scope)
            for member, member_scope in zip(members, member_scopes, strict=True)
        }
        # Only an edge written here gets its cap rows: an existing edge keeps its cap.
        inserted = (
            await self._sess.execute(
                pg_insert(EntityMembershipRow)
                .values([
                    {
                        "virtual_entity_id": virtual_entity_id,
                        "member_entity_id": member_node_id,
                        "capped": cap is not None,
                    }
                    for member_node_id, cap in caps.items()
                ])
                .on_conflict_do_nothing(index_elements=["virtual_entity_id", "member_entity_id"])
                .returning(EntityMembershipRow.id, EntityMembershipRow.member_entity_id)
            )
        ).all()
        cap_values = [
            {"membership_id": row.id, "permission": bit, "all_fields": True}
            for row in inserted
            if (cap := caps[row.member_entity_id]) is not None
            for bit in Permission
            if bit and cap & bit
        ]
        if cap_values:
            await self._sess.execute(pg_insert(EntityMembershipCapRow).values(cap_values))

    async def _associate_entities_with_scope(
        self,
        scope: ScopeRef,
        refs: Sequence[EntityRef],
    ) -> None:
        """Write each entity's legacy scope association."""
        await self._bulk_create_ignore_conflicts([
            self._association_spec(scope, ref) for ref in refs
        ])

    async def _bind_scope_to_member_vs(
        self,
        scope: ScopeRef,
        member_scopes: Sequence[ScopeRef],
    ) -> None:
        """Bind the scope into each member's own virtual entity, uncapped; raises
        :class:`VirtualEntityNotFound` for a scope or member without one."""
        virtual_entity_ids = await self._resolve_virtual_entity_ids([*member_scopes, scope])
        await self._bulk_create_dependent_ignore_conflicts(
            [
                ScopeBindingCreatorSpec(
                    anchor_scope=member_scope, bound_scope=scope, permission_cap=None
                )
                for member_scope in member_scopes
            ],
            virtual_entity_ids,
        )

    @staticmethod
    def _member_scope_ref(ref: EntityRef) -> ScopeRef:
        """The member's own scope identity — every entity doubles as a scope."""
        return ScopeRef(scope_type=ScopeType(ref.entity_type), scope_id=ref.entity_id)

    @staticmethod
    def _association_spec(scope: ScopeRef, ref: EntityRef) -> AssociationScopesEntitiesCreatorSpec:
        return AssociationScopesEntitiesCreatorSpec(
            scope_id=ScopeId(
                scope_type=LegacyScopeType(scope.scope_type),
                scope_id=str(scope.scope_id),
            ),
            object_id=ObjectId(
                entity_type=LegacyEntityType(ref.entity_type),
                entity_id=str(ref.entity_id),
            ),
        )

    async def _grant_member_auto_assign_roles(
        self,
        scope: ScopeRef,
        members: Sequence[ScopeMember],
    ) -> None:
        role_user_ids = [
            user_id for member in members if (user_id := member.assign_role_on()) is not None
        ]
        if role_user_ids:
            await self._grant_auto_assign_roles(
                ScopeId(
                    scope_type=LegacyScopeType(scope.scope_type),
                    scope_id=str(scope.scope_id),
                ),
                role_user_ids,
            )

    async def remove_bulk_members(
        self,
        scope: ScopeRef,
        entities: Collection[EntityRef],
    ) -> None:
        """Detach each member from the scope, undoing both :meth:`add_bulk_members` and
        :meth:`add_bulk_inheriting_members`: the membership, the association, and the scope's
        binding in the member's own virtual entity — a no-op for members added without
        that binding, since the delete matches the scope exactly. Role mappings are left
        untouched. Missing virtual entities (legacy data) never raise — whatever exists is
        deleted.
        """
        entity_refs = list(entities)
        if not entity_refs:
            return
        virtual_entity_id = await self._find_virtual_entity_id(scope)
        member_virtual_entity_ids = await self._find_virtual_entity_ids([
            self._member_scope_ref(ref) for ref in entity_refs
        ])
        if virtual_entity_id is not None and member_virtual_entity_ids:
            await self._sess.execute(
                sa.delete(EntityMembershipRow).where(
                    EntityMembershipRow.virtual_entity_id == virtual_entity_id,
                    EntityMembershipRow.member_entity_id.in_(member_virtual_entity_ids.values()),
                )
            )
        await self._sess.execute(
            sa.delete(AssociationScopesEntitiesRow).where(
                AssociationScopesEntitiesRow.scope_type == LegacyScopeType(scope.scope_type),
                AssociationScopesEntitiesRow.scope_id == str(scope.scope_id),
                sa.tuple_(
                    AssociationScopesEntitiesRow.entity_type,
                    AssociationScopesEntitiesRow.entity_id,
                ).in_([
                    (LegacyEntityType(ref.entity_type), str(ref.entity_id)) for ref in entity_refs
                ]),
            )
        )
        if virtual_entity_id is not None and member_virtual_entity_ids:
            await self._sess.execute(
                sa.delete(ScopeBindingRow).where(
                    ScopeBindingRow.virtual_entity_id.in_(member_virtual_entity_ids.values()),
                    ScopeBindingRow.scope_entity_id == virtual_entity_id,
                )
            )

    # -- Virtual entity: ensure compatibility for externally-created rows ----------

    async def ensure_scope(self, scope: ScopeRef) -> None:
        """Ensure the virtual entity node for an already-created ``scope``. Idempotent."""
        await self._insert_virtual_entities([scope])


class RBACOpsProvider(DBOpsProvider):
    """Hands out :class:`RBACWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncIterator[RBACWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield RBACWriteOps(sess)
