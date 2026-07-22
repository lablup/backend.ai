from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.purger import PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class RolePurgerSpec(PurgerSpec[RoleRow]):
    """PurgerSpec for deleting a role."""

    role_id: uuid.UUID

    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.role_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class PermissionPurgerSpec(PurgerSpec[PermissionRow]):
    """PurgerSpec for deleting a permission."""

    permission_id: uuid.UUID

    @override
    def row_class(self) -> type[PermissionRow]:
        return PermissionRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.permission_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ObjectPermissionPurgerSpec(PurgerSpec[ObjectPermissionRow]):
    """PurgerSpec for deleting an object permission."""

    object_permission_id: uuid.UUID

    @override
    def row_class(self) -> type[ObjectPermissionRow]:
        return ObjectPermissionRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.object_permission_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
