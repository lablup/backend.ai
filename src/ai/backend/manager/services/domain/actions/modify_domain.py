from dataclasses import dataclass, field, fields
from typing import Any, Optional, cast, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData
from ai.backend.manager.types import OptionalState, State, TriState


@dataclass
class ModifyDomainAction(DomainAction):
    domain_name: str
    name: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("name")
    )  # Set if Name for the domain needs to be changed
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

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"

    def get_modified_fields(self) -> dict[str, Any]:
        result = {}
        for f in fields(self):
            if f.name == "domain_name":
                continue
            field_value: TriState = getattr(self, f.name)
            if field_value.state() != State.NOP:
                result[f.name] = cast(Any, field_value.value())
        return result


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool = field(compare=False)
    description: Optional[str] = field(compare=False)

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name if self.domain_data is not None else None
