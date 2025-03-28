import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import ResourceSlot, Sentinel
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.groups.actions.base import GroupAction
from ai.backend.manager.services.groups.types import GroupData


@dataclass
class ModifyGroupAction(GroupAction):
    group_id: uuid.UUID
    name: Optional[str] | Sentinel = Sentinel.TOKEN
    description: Optional[str] | Sentinel = Sentinel.TOKEN
    is_active: Optional[bool] | Sentinel = Sentinel.TOKEN
    domain_name: Optional[str] | Sentinel = Sentinel.TOKEN
    total_resource_slots: Optional[ResourceSlot] | Sentinel = Sentinel.TOKEN
    user_update_mode: Optional[str] | Sentinel = Sentinel.TOKEN
    user_uuids: Optional[list[str]] | Sentinel = Sentinel.TOKEN
    allowed_vfolder_hosts: Optional[dict[str, str]] | Sentinel = Sentinel.TOKEN
    integration_id: Optional[str] | Sentinel = Sentinel.TOKEN
    resource_policy: Optional[str] | Sentinel = Sentinel.TOKEN
    container_registry: Optional[dict[str, str]] | Sentinel = Sentinel.TOKEN

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"

    def get_modified_fields(self) -> dict[str, Any]:
        return {
            k: v for k, v in self.__dict__.items() if v is not Sentinel.TOKEN and k != "group_id"
        }


@dataclass
class ModifyGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None
