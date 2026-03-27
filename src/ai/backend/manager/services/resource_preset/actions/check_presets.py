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
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class CheckResourcePresetsAction(ResourcePresetAction):
    access_key: AccessKey
    resource_policy: Mapping[str, Any]
    domain_name: str
    user_id: uuid.UUID
    group: str
    scaling_group: str | None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class CheckResourcePresetsActionResult(BaseActionResult):
    presets: list[Mapping[str, Any]]
    keypair_limits: list[SlotQuantity]
    keypair_using: list[SlotQuantity]
    keypair_remaining: list[SlotQuantity]
    group_limits: list[SlotQuantity]
    group_using: list[SlotQuantity]
    group_remaining: list[SlotQuantity]
    scaling_group_remaining: list[SlotQuantity]
    scaling_groups: Mapping[str, Mapping[ResourceSlotState, list[SlotQuantity]]]

    # TODO: Should return preset row ids after changing to batching.
    @override
    def entity_id(self) -> str | None:
        return None
