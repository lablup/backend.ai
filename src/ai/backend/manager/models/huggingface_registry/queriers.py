from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryConnectionData
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkHuggingFaceRegistryQuerier(
    BulkEntityQuerier[HuggingFaceRegistryRow, HuggingFaceRegistryConnectionData]
):
    """The HuggingFace registries the caller named."""

    @override
    def row_class(self) -> type[HuggingFaceRegistryRow]:
        return HuggingFaceRegistryRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return HuggingFaceRegistryRow.id

    @override
    def to_data(self, row: HuggingFaceRegistryRow) -> HuggingFaceRegistryConnectionData:
        return HuggingFaceRegistryConnectionData(
            id=ArtifactRegistryID(row.id), url=row.url, token=row.token
        )
