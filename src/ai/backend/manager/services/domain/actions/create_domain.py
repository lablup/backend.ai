from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData


@dataclass
class CreateDomainAction(DomainAction):
    name: str
    description: Optional[str] = ""
    is_active: Optional[bool] = True
    total_resource_slots: Optional[ResourceSlot] = field(
        default_factory=lambda: ResourceSlot.from_user_input({}, None)
    )
    allowed_vfolder_hosts: Optional[dict[str, str]] = field(default_factory=dict)
    allowed_docker_registries: Optional[list[str]] = field(default_factory=list)
    integration_id: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"

    def get_insert_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "allowed_docker_registries": self.allowed_docker_registries,
            "integration_id": self.integration_id,
        }


@dataclass
class CreateDomainActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool = field(compare=False)
    description: Optional[str] = field(compare=False)

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name if self.domain_data is not None else None
