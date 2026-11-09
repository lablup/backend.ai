from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.prometheus_query_preset_category.searchable_fields import (
    PrometheusQueryPresetCategorySearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInPublic
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("PrometheusQueryPresetCategoryUpserter",)


@dataclass
class PrometheusQueryPresetCategoryUpserter(
    CreatedInPublic[PrometheusQueryPresetCategoryRow],
    EntityUpserter[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData],
):
    """Write a query preset category under its stated id. Conflict key: id."""

    id: PrometheusQueryPresetCategoryID
    name: str
    description: str | None

    @override
    def entity_id(self, row: PrometheusQueryPresetCategoryRow) -> PrometheusQueryPresetCategoryID:
        return PrometheusQueryPresetCategoryID(row.id)

    @override
    def row_class(self) -> type[PrometheusQueryPresetCategoryRow]:
        return PrometheusQueryPresetCategoryRow

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
        return {"name": self.name, "description": self.description}

    @override
    def to_data(self, row: PrometheusQueryPresetCategoryRow) -> PrometheusQueryPresetCategoryData:
        return PrometheusQueryPresetCategorySearchableFields.own.to_data(row)
