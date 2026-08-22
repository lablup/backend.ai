import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import (
    AccessKey,
    SlotQuantity,
)
from ai.backend.common.types import (
    LegacyResourceSlotState as ResourceSlotState,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class CheckResourcePresetsAction(ResourcePresetAction):
    access_key: AccessKey
    resource_policy: Mapping[str, Any]
    domain_name: str
    user_id: uuid.UUID
    group: str
    resource_group: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_check_resource_presets"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class CheckResourcePresetsActionResult:
    presets: list[Mapping[str, Any]]
    keypair_limits: list[SlotQuantity]
    keypair_using: list[SlotQuantity]
    keypair_remaining: list[SlotQuantity]
    group_limits: list[SlotQuantity]
    group_using: list[SlotQuantity]
    group_remaining: list[SlotQuantity]
    resource_group_remaining: list[SlotQuantity]
    resource_groups: Mapping[str, Mapping[ResourceSlotState, list[SlotQuantity]]]

    # TODO: Should return preset row ids after changing to batching.
