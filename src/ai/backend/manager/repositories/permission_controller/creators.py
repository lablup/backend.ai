"""CreatorSpec implementations for permission-related entities.

Deprecated: roles and their permissions use the v2 specs under
``models/rbac_models/``; the graph rows (memberships, bindings, role grants) are
written by the ops primitives in ``repositories/ops/v2/`` from whole declarations,
with no spec lineage (BEP-1077).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.types import (
    Permission,
)
from ai.backend.manager.errors.permission import RoleAlreadyAssigned
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class PermissionCreatorSpec(CreatorSpec[PermissionRow]):
    """CreatorSpec for permissions.

    Deprecated: use ``RolePermissionCreator`` in
    ``models/rbac_models/permission/creators.py`` — BA-7204.
    """

    role_id: uuid.UUID
    entity_type: EntityType
    permission: Permission

    @override
    def build_row(self) -> PermissionRow:
        return PermissionRow(
            role_id=self.role_id,
            entity_type=self.entity_type,
            permission=single_bit(self.permission),
        )


@dataclass
class UserRoleCreatorSpec(CreatorSpec[UserRoleRow]):
    """CreatorSpec for user role mappings.

    Deprecated: role grants are written by ``V2EntityWriteOps`` in
    ``repositories/ops/v2/entity_write.py`` — BA-7204.
    """

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
