from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.services.groups.actions.base import GroupAction
from ai.backend.manager.services.groups.types import GroupData


@dataclass
class CreateGroupAction(GroupAction):
    name: str
    domain_name: str
    type: Optional[ProjectType] = ProjectType.GENERAL
    description: Optional[str] = ""
    is_active: Optional[bool] = True
    total_resource_slots: Optional[ResourceSlot] = field(
        default_factory=lambda: ResourceSlot.from_user_input({}, None)
    )
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

    def get_insertion_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain_name": self.domain_name,
            "type": self.type,
            "description": self.description,
            "is_active": self.is_active,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "integration_id": self.integration_id,
            "resource_policy": self.resource_policy,
            "container_registry": self.container_registry,
        }


@dataclass
class CreateGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return self.data.name if self.data is not None else None
