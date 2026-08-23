"""Legacy execution plumbing for the user insert spec.

The spec itself is :class:`ai.backend.manager.models.user.creators.UserCreator`.
Creating a user provisions its default keypair and its domain/project enrollments in
the same transaction, which the v2 ops have no primitive for, so the write still runs
through the RBAC scope creation below.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.ops.rbac.provider import ScopeCreation
from ai.backend.manager.repositories.permission_controller.role_manager import (
    ScopeSystemRoleData,
    UserSystemRoleSpec,
)


@dataclass
class _UserRowInsert(CreatorSpec[UserRow]):
    """Legacy view of :class:`UserCreator`, for the RBAC scope creation executor."""

    creator: UserCreator

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return self.creator.integrity_error_checks()

    @override
    def build_row(self) -> UserRow:
        return self.creator.build_row()


@dataclass
class UserScopeCreation(ScopeCreation[UserRow]):
    """Creates a user row and the scope the user becomes; the user is granted its own
    scope's roles. Domain/project scope associations are written by the enrollment
    step, not by this creator."""

    spec: UserCreator

    @override
    def creator(self) -> RBACEntityCreator[UserRow]:
        return RBACEntityCreator(
            spec=_UserRowInsert(creator=self.spec),
            element_type=RBACElementType.USER,
            scope_ref=None,
        )

    @override
    def scope_of(self, row: UserRow) -> ScopeRef:
        return ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=UserID(row.uuid))

    @override
    def system_roles_of(self, row: UserRow) -> Collection[ScopeSystemRoleData]:
        return (UserSystemRoleSpec(user_id=row.uuid),)


@dataclass
class UserCreateSpec:
    """Specification for creating a single user, including group assignments."""

    creator: UserCreator
    group_ids: list[str] | None = None
