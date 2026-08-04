"""CreatorSpec implementations for permission-related entities."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityRef, ScopeRef
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
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
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.repositories.base.creator import CreatorSpec, DependentCreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


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
    scope_type: RBACElementType
    scope_id: str
    entity_type: RBACElementType
    operation: OperationType

    @override
    def build_row(self) -> PermissionRow:
        return PermissionRow(
            role_id=self.role_id,
            scope_type=self.scope_type.to_scope_type(),
            scope_id=self.scope_id,
            entity_type=self.entity_type.to_entity_type(),
            operation=self.operation,
            permission=Permission.from_operation(self.operation),
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
    granted_by: uuid.UUID | None = None

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
class EntityMembershipCreatorSpec(DependentCreatorSpec[VirtualScopeID, EntityMembershipRow]):
    """Membership of an entity in a virtual scope; the virtual scope id is resolved
    by the caller at execution time and passed as the dependency."""

    entity_ref: EntityRef
    permission_cap: Permission | None = None

    @override
    def build_row(self, dependency: VirtualScopeID) -> EntityMembershipRow:
        return EntityMembershipRow(
            virtual_scope_id=dependency,
            entity_type=self.entity_ref.entity_type,
            entity_id=self.entity_ref.entity_id,
            permission_cap=self.permission_cap,
        )


@dataclass
class ScopeBindingCreatorSpec(
    DependentCreatorSpec[Mapping[ScopeRef, VirtualScopeID], ScopeBindingRow]
):
    """Binding of ``scope`` into ``owner``'s virtual scope; the owner→virtual-scope-id
    mapping is resolved by the caller at execution time and passed as the dependency."""

    owner: ScopeRef
    scope: ScopeRef
    permission_cap: Permission | None = None

    @override
    def build_row(self, dependency: Mapping[ScopeRef, VirtualScopeID]) -> ScopeBindingRow:
        return ScopeBindingRow(
            virtual_scope_id=dependency[self.owner],
            scope_type=self.scope.scope_type,
            scope_id=self.scope.scope_id,
            permission_cap=self.permission_cap,
        )
