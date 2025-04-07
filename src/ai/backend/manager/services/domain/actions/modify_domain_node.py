from dataclasses import dataclass, field, fields
from typing import Any, Optional, cast, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, UserInfo
from ai.backend.manager.types import OptionalState, State, TriState


@dataclass
class ModifyDomainNodeAction(DomainAction):
    name: str
    user_info: UserInfo
    description: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    total_resource_slots: TriState[Optional[ResourceSlot]] = field(
        default_factory=lambda: TriState.nop("total_resource_slots")
    )
    allowed_vfolder_hosts: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_vfolder_hosts")
    )
    allowed_docker_registries: OptionalState[list[str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_docker_registries")
    )
    integration_id: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("integration_id")
    )
    dotfiles: OptionalState[bytes] = field(default_factory=lambda: OptionalState.nop("dotfiles"))
    sgroups_to_add: OptionalState[set[str]] = field(
        default_factory=lambda: OptionalState.nop("scaling_groups")
    )
    sgroups_to_remove: OptionalState[set[str]] = field(
        default_factory=lambda: OptionalState.nop("scaling_groups")
    )

    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "modify"

    def get_modified_fields(self) -> dict[str, Any]:
        exclude_fields = [
            "name",
            "user_info",
            "sgroups_to_add",
            "sgroups_to_remove",
        ]
        result = {}
        for f in fields(self):
            if f.name in exclude_fields:
                continue
            field_value: OptionalState = getattr(self, f.name)
            if field_value.state() != State.NOP:
                result[f.name] = cast(Any, field_value.value())
        return result


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool
    description: Optional[str]

    @override
    def entity_id(self):
        return self.domain_data.name if self.domain_data is not None else None
