from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ContainerRegistryAction(BaseGlobalAction):
    """Base for an operation that names no single container registry."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ContainerRegistryEntityType()


@dataclass
class ContainerRegistrySingleEntityAction(BaseSingleEntityAction):
    """Base for an operation on one container registry."""

    registry_id: ContainerRegistryID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.registry_id
