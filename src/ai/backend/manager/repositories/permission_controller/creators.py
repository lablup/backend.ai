"""CreatorSpec implementations for permission-related entities."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.status import PermissionStatus, RoleStatus
from ai.backend.manager.data.permission.types import (
    OperationType,
    Permission,
    RoleSource,
)
from ai.backend.manager.errors.permission import RoleAlreadyAssigned
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.repositories.base.creator import CreatorSpec, DependentCreatorSpec


@dataclass
class RoleCreatorSpec(CreatorSpec[RoleRow]):
    """CreatorSpec for role creation.

    Only defines the role itself. Object permissions
    are passed separately to create_role() for better separation of concerns.
    """

    name: str
    source: RoleSource
    status: RoleStatus
    description: str | None = None
    auto_assign: bool = False

    @override
    def build_row(self) -> RoleRow:
        return RoleRow(
            name=self.name,
            source=self.source,
            status=self.status,
            description=self.description,
            auto_assign=self.auto_assign,
        )


@dataclass
class PermissionCreatorSpec(CreatorSpec[PermissionRow]):
    """CreatorSpec for permissions."""

    role_id: uuid.UUID
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    permission: Permission

    @override
    def build_row(self) -> PermissionRow:
        return PermissionRow(
            role_id=self.role_id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            entity_type=self.entity_type,
            permission=single_bit(self.permission),
        )


@dataclass
class ObjectPermissionCreatorSpec(CreatorSpec[ObjectPermissionRow]):
    """CreatorSpec for object permissions."""

    role_id: uuid.UUID
    entity_type: RBACElementType
    entity_id: str
    operation: OperationType
    status: PermissionStatus = PermissionStatus.ACTIVE

    @override
    def build_row(self) -> ObjectPermissionRow:
        return ObjectPermissionRow(
            role_id=self.role_id,
            entity_type=self.entity_type.to_entity_type(),
            entity_id=self.entity_id,
            operation=self.operation,
        )


@dataclass
class UserRoleCreatorSpec(CreatorSpec[UserRoleRow]):
    """CreatorSpec for user role mappings."""

    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: UserID | None = None

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=RoleAlreadyAssigned(
                    f"Role {self.role_id} is already assigned to user {self.user_id}."
                ),
            ),
        )

    @override
    def build_row(self) -> UserRoleRow:
        row = UserRoleRow(
            user_id=self.user_id,
            role_id=self.role_id,
        )
        if self.granted_by is not None:
            row.granted_by = self.granted_by
        return row


@dataclass
class AssociationScopesEntitiesCreatorSpec(CreatorSpec[AssociationScopesEntitiesRow]):
    """CreatorSpec for association between scopes and entities."""

    scope_id: ScopeId
    object_id: ObjectId

    @override
    def build_row(self) -> AssociationScopesEntitiesRow:
        return AssociationScopesEntitiesRow(
            scope_type=self.scope_id.scope_type,
            scope_id=self.scope_id.scope_id,
            entity_type=self.object_id.entity_type,
            entity_id=self.object_id.entity_id,
        )


@dataclass
class EntityMembershipCreatorSpec(DependentCreatorSpec[VirtualEntityID, EntityMembershipRow]):
    """Membership of the entity behind ``member_entity_id`` in the virtual entity given
    as the dependency."""

    member_entity_id: VirtualEntityID
    permission_cap: Permission | None = None

    @override
    def build_row(self, dependency: VirtualEntityID) -> EntityMembershipRow:
        return EntityMembershipRow(
            virtual_entity_id=dependency,
            member_entity_id=self.member_entity_id,
            permission_cap=self.permission_cap,
        )


@dataclass
class ScopeBindingCreatorSpec(
    DependentCreatorSpec[Mapping[ScopeRef, VirtualEntityID], ScopeBindingRow]
):
    """Binding of ``bound_scope`` into ``anchor_scope``'s virtual entity; the dependency
    maps both scopes to their virtual entity ids."""

    anchor_scope: ScopeRef
    bound_scope: ScopeRef
    permission_cap: Permission | None = None

    @override
    def build_row(self, dependency: Mapping[ScopeRef, VirtualEntityID]) -> ScopeBindingRow:
        return ScopeBindingRow(
            virtual_entity_id=dependency[self.anchor_scope],
            scope_entity_id=dependency[self.bound_scope],
            permission_cap=self.permission_cap,
        )
