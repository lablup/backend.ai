import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.groups.actions.base import GroupAction
from ai.backend.manager.services.groups.types import GroupData


@dataclass
class ModifyGroupAction(GroupAction):
    group_id: uuid.UUID
    name: Optional[str]
    description: Optional[str]
    is_active: Optional[bool]
    domain_name: Optional[str]
    total_resource_slots: Optional[ResourceSlot]
    user_update_mode: Optional[str]
    user_uuids: Optional[list[str]]
    allowed_vfolder_hosts: Optional[dict[str, str]]
    integration_id: Optional[str]
    resource_policy: Optional[str]
    container_registry: Optional[dict[str, str]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class ModifyGroupActionResult(BaseActionResult):
    data: Optional[GroupData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None
