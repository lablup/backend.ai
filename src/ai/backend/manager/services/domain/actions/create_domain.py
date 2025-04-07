from dataclasses import dataclass, field
from typing import Any, Optional, cast, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData
from ai.backend.manager.types import OptionalState, State, TriState


@dataclass
class CreateDomainAction(DomainAction):
    name: str
    description: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    total_resource_slots: TriState[ResourceSlot] = field(
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
        ]

        for field_name in optional_fields:
            field_value: TriState = getattr(self, field_name)
            if field_value.state() != State.NOP:
                result[field_name] = cast(Any, field_value.value())

        return result


@dataclass
class CreateDomainActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool = field(compare=False)
    description: Optional[str] = field(compare=False)

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name if self.domain_data is not None else None
