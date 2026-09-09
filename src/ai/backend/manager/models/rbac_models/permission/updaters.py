from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class RolePermissionUpdater(DataUpdater[PermissionRow, PermissionData]):
    """Updater for one permission entry of a role."""

    permission_id: PermissionID
    entity_type: OptionalState[EntityType] = field(default_factory=OptionalState.nop)
    permission: OptionalState[Permission] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[PermissionRow]:
        return PermissionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return PermissionRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.permission_id

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.entity_type.update_dict(to_update, "entity_type")
        if (permission := self.permission.optional_value()) is not None:
            to_update["permission"] = single_bit(permission)
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: PermissionRow) -> PermissionData:
        return row.to_data()
