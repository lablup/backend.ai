from dataclasses import dataclass, field
from typing import Any, Optional, cast, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.services.groups.actions.base import GroupAction
from ai.backend.manager.services.groups.types import GroupData
from ai.backend.manager.types import OptionalState, State, TriState


@dataclass
class CreateGroupAction(GroupAction):
    name: str
    domain_name: str
    type: OptionalState[ProjectType] = field(default_factory=lambda: OptionalState.nop("type"))
    description: OptionalState[Optional[str]] = field(
        default_factory=lambda: OptionalState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    total_resource_slots: OptionalState[Optional[ResourceSlot]] = field(
        default_factory=lambda: OptionalState.nop("total_resource_slots")
    )
    allowed_vfolder_hosts: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_vfolder_hosts")
    )
    integration_id: OptionalState[Optional[str]] = field(
        default_factory=lambda: OptionalState.nop("integration_id")
    )
    resource_policy: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("resource_policy")
    )
    container_registry: OptionalState[Optional[dict[str, str]]] = field(
        default_factory=lambda: OptionalState.nop("container_registry")
    )

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
            field_value: TriState = getattr(self, field_name)
            if field_value.state() != State.NOP:
                result[field_name] = cast(Any, field_value.value())

        return result


@dataclass
class CreateGroupActionResult(BaseActionResult):
    data: Optional[GroupData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return self.data.name if self.data is not None else None
