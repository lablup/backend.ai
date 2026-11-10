from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeGlobalEntityOpsAction
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.purgers import ContainerRegistryPurger
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow


@dataclass(frozen=True)
class PartialBulkPurgeContainerRegistriesAction(
    PartialBulkPurgeGlobalEntityOpsAction[ContainerRegistryRow, ContainerRegistryData]
):
    """Remove the named container registries, answering for each one."""

    ids: Sequence[ContainerRegistryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_container_registries"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, ContainerRegistryPurger]:
        return {
            registry_id: ContainerRegistryPurger(registry_id=registry_id)
            for registry_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, ids=[registry_id for registry_id in self.ids if registry_id in allowed]
        )
