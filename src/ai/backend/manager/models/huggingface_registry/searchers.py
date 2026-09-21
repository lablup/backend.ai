"""Searcher spec for the huggingface_registries table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import with_expression

from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.huggingface_registry.searchable_fields import (
    HuggingFaceRegistrySearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class HuggingFaceRegistrySearcher(Searcher[HuggingFaceRegistryRow, HuggingFaceRegistryData]):
    """The name is the artifact_registries row's, so every read joins it."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(HuggingFaceRegistryRow)
            .join(
                ArtifactRegistryRow,
                ArtifactRegistryRow.registry_id == HuggingFaceRegistryRow.id,
            )
            .options(
                with_expression(HuggingFaceRegistryRow.registry_name, ArtifactRegistryRow.name)
            )
        )

    @override
    def to_data(self, row: HuggingFaceRegistryRow) -> HuggingFaceRegistryData:
        return HuggingFaceRegistrySearchableFields.own.to_data(row)
