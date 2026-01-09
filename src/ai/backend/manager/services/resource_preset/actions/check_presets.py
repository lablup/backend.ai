import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import (
    AccessKey,
    ResourceSlot,
)
from ai.backend.common.types import (
    LegacyResourceSlotState as ResourceSlotState,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class CheckResourcePresetsAction(ResourcePresetAction):
    access_key: AccessKey
    resource_policy: Mapping[str, Any]
    domain_name: str
    user_id: uuid.UUID
    group: str
    scaling_group: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "check_multi"


@dataclass
class CheckResourcePresetsActionResult(BaseActionResult):
    presets: list[Mapping[str, Any]]
    keypair_limits: ResourceSlot
    keypair_using: ResourceSlot
    keypair_remaining: ResourceSlot
    group_limits: ResourceSlot
    group_using: ResourceSlot
    group_remaining: ResourceSlot
    scaling_group_remaining: ResourceSlot
    scaling_groups: Mapping[str, Mapping[ResourceSlotState, ResourceSlot]]

    # TODO: Should return preset row ids after changing to batching.
    @override
    def entity_id(self) -> Optional[str]:
        return None
