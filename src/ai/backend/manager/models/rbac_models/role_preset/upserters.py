from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.searchable_fields import (
    RolePresetSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("RolePresetUpserter",)


@dataclass
class RolePresetUpserter(
    CreatedInGlobal[RolePresetRow], EntityUpserter[RolePresetRow, RolePresetData]
):
    """Write a role preset under its stated id, restoring a deleted one.

    Conflict key: id. ``role_name_template`` and ``scope_id`` are left as they are.
    """

    id: RolePresetID
    name: str
    scope_type: EntityType
    auto_assign: bool

    @override
    def entity_id(self, row: RolePresetRow) -> RolePresetID:
        return RolePresetID(row.id)

    @override
    def row_class(self) -> type[RolePresetRow]:
        return RolePresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "scope_type": self.scope_type,
            "auto_assign": self.auto_assign,
            "deleted": False,
        }

    @override
    def to_data(self, row: RolePresetRow) -> RolePresetData:
        return RolePresetSearchableFields.own.to_data(row)
