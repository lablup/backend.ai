from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryModifierMeta
from ai.backend.manager.models.reservoir_registry.updaters import ReservoirRegistryUpdater


@dataclass(frozen=True)
class PartialBulkUpdateReservoirRegistryItem:
    """One registry of a partial bulk update: its settings and its name."""

    updater: ReservoirRegistryUpdater
    meta: ArtifactRegistryModifierMeta

    @property
    def registry_id(self) -> ArtifactRegistryID:
        return self.updater.registry_id


@dataclass(frozen=True)
class PartialBulkUpdateReservoirRegistriesAction(BasePartialBulkAction):
    """Edit the named Reservoir registries, answering for each one."""

    items: Sequence[PartialBulkUpdateReservoirRegistryItem]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_reservoir_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(item.registry_id for item in self.items)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, items=[item for item in self.items if item.registry_id in allowed])
