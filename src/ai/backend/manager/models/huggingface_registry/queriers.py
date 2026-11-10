from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryConnectionData
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.huggingface_registry.searchable_fields import (
    HuggingFaceRegistrySearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkHuggingFaceRegistryQuerier(
    BulkEntityQuerier[HuggingFaceRegistryRow, HuggingFaceRegistryConnectionData]
):
    """The HuggingFace registries the caller named, without the name the meta row holds."""

    @override
    def row_class(self) -> type[HuggingFaceRegistryRow]:
        return HuggingFaceRegistryRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return HuggingFaceRegistryRow.id

    @override
    def to_data(self, row: HuggingFaceRegistryRow) -> HuggingFaceRegistryConnectionData:
        own = HuggingFaceRegistrySearchableFields.own
        return HuggingFaceRegistryConnectionData(
            id=ArtifactRegistryID(own.id.read(row)),
            url=own.url.read(row),
            token=own.token.read(row),
        )
