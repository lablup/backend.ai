"""What a HuggingFace registry search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.exception import RelationNotLoadedError
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.artifact_registries.searchable_fields import (
    ArtifactRegistrySearchableFields,
)
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToOneCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField


class _HuggingFaceRegistryOwnFields(
    RowDataConverter[HuggingFaceRegistryRow, HuggingFaceRegistryData]
):
    """The HuggingFace registry's own columns. ``name`` is the meta row's, declared in ``nested``."""

    id = SearchableField(
        HuggingFaceRegistryRow.id,
        UUIDConditions(HuggingFaceRegistryRow.id),
        ColumnOrder(HuggingFaceRegistryRow.id),
    )
    url = SearchableField(
        HuggingFaceRegistryRow.url,
        StringConditions(HuggingFaceRegistryRow.url),
        ColumnOrder(HuggingFaceRegistryRow.url),
    )
    token = SearchableField(HuggingFaceRegistryRow.token, None, None)
    """Sensitive: the plaintext token the manager authenticates to the registry with."""

    @override
    def to_data(self, row: HuggingFaceRegistryRow) -> HuggingFaceRegistryData:
        meta = row.meta
        if meta is None:
            raise RelationNotLoadedError()
        return HuggingFaceRegistryData(
            id=self.id.read(row),
            name=ArtifactRegistrySearchableFields.own.name.read(meta),
            url=self.url.read(row),
            token=self.token.read(row),
        )


class _HuggingFaceRegistryNestedFields:
    """The artifact registry row this registry's name lives in."""

    meta = NestedSearchableField(
        ArtifactRegistrySearchableFields.own,
        ToOneCorrelation(
            ArtifactRegistryRow,
            HuggingFaceRegistryRow,
            ArtifactRegistryRow.registry_id == HuggingFaceRegistryRow.id,
        ),
    )


class HuggingFaceRegistrySearchableFields:
    own = _HuggingFaceRegistryOwnFields()
    nested = _HuggingFaceRegistryNestedFields
