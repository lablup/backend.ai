from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryConnectionData
from ai.backend.manager.models.huggingface_registry.queriers import BulkHuggingFaceRegistryQuerier
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow


@dataclass
class BulkGetHuggingFaceRegistriesAction(
    PartialBulkGetEntityOpsAction[HuggingFaceRegistryRow, HuggingFaceRegistryConnectionData]
):
    """Read the HuggingFace registries the caller named, answering for each id."""

    ids: Sequence[ArtifactRegistryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_hugging_face_registries"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkHuggingFaceRegistryQuerier:
        return BulkHuggingFaceRegistryQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
