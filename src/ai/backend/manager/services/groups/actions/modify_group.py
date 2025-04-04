import uuid
from dataclasses import dataclass, field, fields
from typing import Any, Optional, cast, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.groups.actions.base import GroupAction
from ai.backend.manager.services.groups.types import GroupData
from ai.backend.manager.types import OptionalState, State


@dataclass
class ModifyGroupAction(GroupAction):
    group_id: uuid.UUID
    name: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("name"))
    description: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    domain_name: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("domain_name")
    )
    total_resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=lambda: OptionalState.nop("total_resource_slots")
    )
    user_update_mode: OptionalState[Optional[str]] = field(
        default_factory=lambda: OptionalState.nop("user_update_mode")
    )
    user_uuids: OptionalState[list[str]] = field(
        default_factory=lambda: OptionalState.nop("user_uuids")
    )
    allowed_vfolder_hosts: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_vfolder_hosts")
    )
    integration_id: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("integration_id")
    )
    resource_policy: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("resource_policy")
    )
    container_registry: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("container_registry")
    )

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"

    def get_modified_fields(self) -> dict[str, Any]:
        result = {}
        for f in fields(self):
            if f.name == "group_id":
                continue
            field_value: OptionalState = getattr(self, f.name)
            if field_value.state() != State.NOP:
                result[f.name] = cast(Any, field_value.value())
        return result


@dataclass
class ModifyGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None
