from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.membership.base import BaseMembershipAction
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.resource_preset.types import ResourcePresetData


@dataclass(frozen=True)
class SetResourcePresetResourceGroupAction(BaseMembershipAction):
    """Bind the preset to a resource group, or to none, which puts it in the `public`
    scope or takes it out."""

    preset_id: ResourcePresetID
    resource_group_name: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "set_resource_preset_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def scopes(self) -> Sequence[EntityIdentifier]:
        return (global_entity_id(GlobalEntityName.PUBLIC),)


@dataclass(frozen=True)
class SetResourcePresetResourceGroupActionResult:
    resource_preset: ResourcePresetData
