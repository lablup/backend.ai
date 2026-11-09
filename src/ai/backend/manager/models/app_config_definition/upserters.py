from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("AppConfigDefinitionUpserter",)


@dataclass
class AppConfigDefinitionUpserter(
    CreatedInGlobal[AppConfigDefinitionRow],
    EntityUpserter[AppConfigDefinitionRow, AppConfigDefinitionData],
):
    """Upserter for one registered config name.

    Conflict key: ``config_name``. The row holds no other value, so an update only bumps
    ``updated_at``.
    """

    config_name: str

    @override
    def entity_id(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionID:
        return AppConfigDefinitionID(row.id)

    @override
    def row_class(self) -> type[AppConfigDefinitionRow]:
        return AppConfigDefinitionRow

    @override
    def index_elements(self) -> list[str]:
        return ["config_name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"config_name": self.config_name}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {"updated_at": sa.func.now()}

    @override
    def to_data(self, row: AppConfigDefinitionRow) -> AppConfigDefinitionData:
        return row.to_data()
