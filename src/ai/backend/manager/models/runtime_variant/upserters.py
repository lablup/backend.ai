from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant.searchable_fields import (
    RuntimeVariantSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInPublic
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("RuntimeVariantUpserter",)


@dataclass
class RuntimeVariantUpserter(
    CreatedInPublic[RuntimeVariantRow], EntityUpserter[RuntimeVariantRow, RuntimeVariantData]
):
    """Write a runtime variant under its stated id. Conflict key: id."""

    id: RuntimeVariantID
    name: str
    description: str | None
    reads_vfolder_config_files: bool
    default_model_definition: DefaultModelDefinition

    @override
    def entity_id(self, row: RuntimeVariantRow) -> RuntimeVariantID:
        return RuntimeVariantID(row.id)

    @override
    def row_class(self) -> type[RuntimeVariantRow]:
        return RuntimeVariantRow

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
            "description": self.description,
            "reads_vfolder_config_files": self.reads_vfolder_config_files,
            "default_model_definition": self.default_model_definition,
        }

    @override
    def to_data(self, row: RuntimeVariantRow) -> RuntimeVariantData:
        return RuntimeVariantSearchableFields.own.to_data(row)
