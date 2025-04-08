import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource.base import ResourceAction


@dataclass
class CheckResourcePresetsAction(ResourceAction):
    access_key: str
    resource_policy: Mapping[str, Any]
    domain_name: str
    user_id: uuid.UUID
    group: str
    scaling_group: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "check_resource_presets"


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

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return ""

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return True
