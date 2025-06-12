import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class CheckResourcePresetsAction(ResourcePresetAction):
    access_key: str
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
    presets: list[Any]
    keypair_limits: Mapping[str, str]
    keypair_using: Mapping[str, str]
    keypair_remaining: Mapping[str, str]
    group_limits: Mapping[str, str]
    group_using: Mapping[str, str]
    group_remaining: Mapping[str, str]
    scaling_group_remaining: Mapping[str, str]
    scaling_groups: dict[str | Any, dict[str, ResourceSlot]]

    # TODO: Should return preset row ids after changing to batching.
    @override
    def entity_id(self) -> Optional[str]:
        return None
