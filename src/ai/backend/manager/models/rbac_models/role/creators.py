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
    """Creator for a custom role, created in the one scope that holds it.

    The row carries the scope; the own and govern edges every other entity's
    ``created_in`` writes are derived from it. Source is not a caller's choice: a
    role made here is custom, and a system role comes only from a preset.
    """

    name: str
    scope: EntityIdentifier
    description: str | None = None
    auto_assign: bool = False
    # The row defaults an omitted status to active.
    status: RoleStatus | None = None

    @override
    def entity_id(self, row: RoleRow) -> RoleID:
        return RoleID(row.id)

    @override
    def created_in(self, row: RoleRow) -> Collection[EntityIdentifier]:
        return (row.scope(),)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> RoleRow:
        row = RoleRow(
            name=self.name,
            source=RoleSource.CUSTOM,
            description=self.description,
            auto_assign=self.auto_assign,
            scope_type=self.scope.entity_type(),
            scope_id=self.scope,
        )
        if self.status is not None:
            row.status = self.status
        return row

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return row.to_data()
