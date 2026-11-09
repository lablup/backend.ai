from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role.searchable_fields import RoleSearchableFields
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("RoleUpserter",)


@dataclass
class RoleUpserter(EntityUpserter[RoleRow, RoleData]):
    """Write a role under its stated id in its scope, restoring a deleted one. Conflict
    key: id. The scope, the preset and the source are written on insert only; the source
    is ``system`` for a role of a preset and ``custom`` otherwise, as the runtime paths."""

    id: RoleID
    name: str
    description: str | None
    scope: EntityIdentifier
    role_preset_id: RolePresetID | None
    auto_assign: bool

    @override
    def entity_id(self, row: RoleRow) -> RoleID:
        return RoleID(row.id)

    @override
    def created_in(self, row: RoleRow) -> Collection[EntityIdentifier]:
        return (row.scope(),)

    @override
    def row_class(self) -> type[RoleRow]:
        return RoleRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scope_type": self.scope.entity_type(),
            "scope_id": self.scope,
            "role_preset_id": self.role_preset_id,
            "source": RoleSource.CUSTOM if self.role_preset_id is None else RoleSource.SYSTEM,
            **self._values(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "auto_assign": self.auto_assign,
            "status": RoleStatus.ACTIVE,
            "deleted_at": None,
        }

    @override
    def to_data(self, row: RoleRow) -> RoleData:
        return RoleSearchableFields.own.to_data(row)
