"""Container-registry search over the domains they are related to."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow

__all__ = ("ScopedSearchContainerRegistriesAction",)


@dataclass(frozen=True)
class ScopedSearchContainerRegistriesAction(
    ScopedSearchOpsAction[ContainerRegistryRow, ContainerRegistryData]
):
    """Page through the container registries the named scopes reach, combined with OR."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ContainerRegistryEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_container_registries"
