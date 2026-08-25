"""Update spec for the huggingface_registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class HuggingFaceRegistryUpdater(DataUpdater[HuggingFaceRegistryRow, HuggingFaceRegistryData]):
    """Edit a HuggingFace registry. The name is the meta row's and is not written here."""

    registry_id: ArtifactRegistryID
    url: OptionalState[str] = field(default_factory=OptionalState.nop)
    token: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[HuggingFaceRegistryRow]:
        return HuggingFaceRegistryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return HuggingFaceRegistryRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.registry_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.url.update_dict(to_update, "url")
        self.token.update_dict(to_update, "token")
        return to_update

    @override
    def to_data(self, row: HuggingFaceRegistryRow) -> HuggingFaceRegistryData:
        return row.to_dataclass()
