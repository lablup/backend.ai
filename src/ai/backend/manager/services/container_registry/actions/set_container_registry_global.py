from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.membership.base import BaseMembershipAction
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.permission.global_entity import global_entity_id


@dataclass(frozen=True)
class SetContainerRegistryGlobalAction(BaseMembershipAction):
    """Put the registry in the `public` scope, or take it out, with `is_global`."""

    registry_id: ContainerRegistryID
    is_global: bool

    @override
    @classmethod
    def action_name(cls) -> str:
        return "set_container_registry_global"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity(self) -> EntityIdentifier:
        return self.registry_id

    @override
    def scopes(self) -> Sequence[EntityIdentifier]:
        return (global_entity_id(GlobalEntityName.PUBLIC),)


@dataclass(frozen=True)
class SetContainerRegistryGlobalActionResult:
    data: ContainerRegistryData
