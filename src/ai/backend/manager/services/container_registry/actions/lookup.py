from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
    ContainerRegistryName,
    ContainerRegistryProjectName,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.container_registry.lookups import (
    ContainerRegistryByNameAndRegistryProjectLookup,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow


@dataclass(frozen=True)
class ContainerRegistryNameProjectKey(LookupKey):
    registry_name: ContainerRegistryName
    registry_project_name: ContainerRegistryProjectName | None

    @override
    def kind(self) -> str:
        return "registry_name_and_project"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"registry": self.registry_name, "project": self.registry_project_name}


@dataclass(frozen=True)
class LookupContainerRegistryAction(
    LookupEntityOpsAction[ContainerRegistryRow, ContainerRegistryID]
):
    registry_name: ContainerRegistryName
    registry_project_name: ContainerRegistryProjectName | None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ContainerRegistryEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_container_registry"

    @override
    def lookup_key(self) -> ContainerRegistryNameProjectKey:
        return ContainerRegistryNameProjectKey(self.registry_name, self.registry_project_name)

    @override
    def to_lookup(self) -> ContainerRegistryByNameAndRegistryProjectLookup:
        return ContainerRegistryByNameAndRegistryProjectLookup(
            self.registry_name, self.registry_project_name
        )
