from dataclasses import dataclass, field
from typing import Any, Optional, cast, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, UserInfo
from ai.backend.manager.types import OptionalState, State, TriState


@dataclass
class CreateDomainNodeAction(DomainAction):
    name: str
    user_info: UserInfo
    description: OptionalState[Optional[str]] = field(
        default_factory=lambda: OptionalState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    total_resource_slots: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("total_resource_slots")
    )
    allowed_vfolder_hosts: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_vfolder_hosts")
    )
    allowed_docker_registries: OptionalState[list[str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_docker_registries")
    )
    integration_id: OptionalState[Optional[str]] = field(
        default_factory=lambda: OptionalState.nop("integration_id")
    )
    dotfiles: OptionalState[bytes] = field(default_factory=lambda: OptionalState.nop("dotfiles"))
    scaling_groups: OptionalState[list[str]] = field(
        default_factory=lambda: OptionalState.nop("scaling_groups")
    )

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"

    def get_insertion_data(self) -> dict[str, Any]:
        result = {"name": self.name}

        optional_fields = [
            "description",
            "is_active",
            "total_resource_slots",
            "allowed_vfolder_hosts",
            "allowed_docker_registries",
            "integration_id",
            "dotfiles",
            "scaling_groups",
        ]

        for field_name in optional_fields:
            field_value: TriState = getattr(self, field_name)
            if field_value.state() != State.NOP:
                result[field_name] = cast(Any, field_value.value())

        return result


@dataclass
class CreateDomainNodeActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool
    description: str

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name if self.domain_data is not None else None
