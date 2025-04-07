from dataclasses import dataclass
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
    type: Optional[ProjectType]
    description: Optional[str]
    is_active: Optional[bool]
    total_resource_slots: Optional[ResourceSlot]
    allowed_vfolder_hosts: Optional[dict[str, str]]
    integration_id: Optional[str]
    resource_policy: Optional[str]
    container_registry: Optional[dict[str, str]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"

    def get_insertion_data(self) -> dict[str, Any]:
        result = {"name": self.name, "domain_name": self.domain_name}

        optional_fields = [
            "type",
            "description",
            "is_active",
            "total_resource_slots",
            "allowed_vfolder_hosts",
            "integration_id",
            "resource_policy",
            "container_registry",
        ]

        for field_name in optional_fields:
            field_value = getattr(self, field_name)
            if field_value is not None:
                result[field_name] = field_value

        return result


@dataclass
class CreateGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return self.data.name if self.data is not None else None
