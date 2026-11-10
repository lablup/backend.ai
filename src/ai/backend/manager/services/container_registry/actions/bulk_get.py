from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.queriers import BulkContainerRegistryQuerier
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow


@dataclass
class BulkGetContainerRegistriesAction(
    PartialBulkGetEntityOpsAction[ContainerRegistryRow, ContainerRegistryData]
):
    """Read the container registries the caller named, answering for each id."""

    ids: Sequence[ContainerRegistryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_container_registries"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkContainerRegistryQuerier:
        return BulkContainerRegistryQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
