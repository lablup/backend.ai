from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class RoleCreator(EntityCreator[RoleRow, RoleData]):
    """Creator for a role, created in the scope that holds it.

    The scope owns and governs the new role, the same pair every other entity's
    ``created_in`` writes; the roles a preset instantiates take the same path.
    """

    name: str
    scope: EntityIdentifier
    source: RoleSource = RoleSource.CUSTOM
    status: RoleStatus = RoleStatus.ACTIVE
    description: str | None = None
    auto_assign: bool = False

    @override
    def entity_id(self, row: RoleRow) -> RoleID:
        return RoleID(row.id)

    @override
    def created_in(self, row: RoleRow) -> Collection[EntityIdentifier]:
        return (self.scope,)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> RoleRow:
        return RoleRow(
            name=self.name,
            source=self.source,
            status=self.status,
            description=self.description,
            auto_assign=self.auto_assign,
        )

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return row.to_data()
