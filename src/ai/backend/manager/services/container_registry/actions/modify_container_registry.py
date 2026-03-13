from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.container_registry.actions.base import (
    ContainerRegistrySingleEntityAction,
    ContainerRegistrySingleEntityActionResult,
)


@dataclass
class ModifyContainerRegistryAction(ContainerRegistrySingleEntityAction):
    updater: Updater[ContainerRegistryRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.CONTAINER_REGISTRY, str(self.updater.pk_value))


@dataclass
class ModifyContainerRegistryActionResult(ContainerRegistrySingleEntityActionResult):
    data: ContainerRegistryData

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id)
