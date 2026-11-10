"""Action for searching container registries."""

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow


@dataclass(frozen=True)
class SearchContainerRegistriesAction(
    GlobalSearcherOpsAction[ContainerRegistryRow, ContainerRegistryData]
):
    """Page through every container registry."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ContainerRegistryEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_container_registries"
