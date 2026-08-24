"""Insert spec for the huggingface_registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class HuggingFaceRegistryCreator(
    GlobalEntityCreator[HuggingFaceRegistryRow, HuggingFaceRegistryData]
):
    """Register a HuggingFace registry.

    The node is provisioned on this row's id: an artifact joins the registry by the id
    its ``registry_id`` carries, which is this row's rather than the
    ``artifact_registries`` row's. The name lives in that other row, so ``to_data``
    reads it through the relation the registry ops loads after writing both.
    """

    url: str
    token: str | None = None

    @override
    def entity_id(self, row: HuggingFaceRegistryRow) -> ArtifactRegistryID:
        return ArtifactRegistryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> HuggingFaceRegistryRow:
        return HuggingFaceRegistryRow(url=self.url, token=self.token)

    @override
    def to_data(self, row: HuggingFaceRegistryRow) -> HuggingFaceRegistryData:
        return row.to_dataclass()
