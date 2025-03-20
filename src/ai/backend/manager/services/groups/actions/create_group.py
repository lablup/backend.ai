from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.groups.base import GroupAction


@dataclass
class CreateGroupAction(GroupAction):
    domain_name: str
    type: Optional[str] = "GENERAL"
    description: Optional[str] = ""
    is_active: Optional[bool] = True
    total_resource_slots: Optional[dict[str, str]] = field(default_factory=dict)
    allowed_vfolder_hosts: Optional[dict[str, str]] = field(default_factory=dict)
    integration_id: Optional[str] = ""
    resource_policy: Optional[str] = "default"
    container_registry: Optional[dict[str, str]] = field(default_factory=dict)

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"


@dataclass
class CreateGroupActionResult(BaseActionResult):
    data: Optional[Any]

    @override
    def entity_id(self) -> Optional[str]:
        return None
