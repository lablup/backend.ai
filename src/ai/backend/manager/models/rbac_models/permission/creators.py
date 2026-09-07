from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import PermissionAlreadyGranted
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class RolePermissionCreator(FieldCreator[RoleID, PermissionRow, PermissionData]):
    """Creator for one permission entry of a role — the operation on every field.

    A field of its role: it grants nothing of its own and dies with the role. An entry
    scoped to field paths is written through the role permission ops instead, which
    settle the parent row and its paths together.
    """

    scope: EntityIdentifier
    entity_type: EntityType
    permission: Permission

    @override
    def field_id(self, row: PermissionRow) -> PermissionID:
        return PermissionID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=PermissionAlreadyGranted(
                    f"Duplicate permission entry ({self.scope}, {self.entity_type},"
                    f" {self.permission})."
                ),
            ),
        )

    @override
    def build_row(self, owner_id: RoleID) -> PermissionRow:
        return PermissionRow(
            role_id=owner_id,
            scope_type=self.scope.entity_type(),
            scope_id=str(self.scope),
            entity_type=self.entity_type,
            permission=single_bit(self.permission),
        )

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return row.to_data()
