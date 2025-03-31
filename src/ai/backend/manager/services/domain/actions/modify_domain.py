from dataclasses import dataclass, field, fields
from typing import Any, Optional, override

from ai.backend.common.types import ResourceSlot, Sentinel
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData


@dataclass
class ModifyDomainAction(DomainAction):
    domain_name: str
    name: Optional[str] | Sentinel = (
        Sentinel.TOKEN
    )  # Set if Name for the domain needs to be changed
    description: Optional[str] | Sentinel = Sentinel.TOKEN
    is_active: Optional[bool] | Sentinel = Sentinel.TOKEN
    total_resource_slots: Optional[ResourceSlot] | Sentinel = Sentinel.TOKEN
    allowed_vfolder_hosts: Optional[dict[str, str]] | Sentinel = Sentinel.TOKEN
    allowed_docker_registries: Optional[list[str]] | Sentinel = Sentinel.TOKEN
    integration_id: Optional[str] | Sentinel = Sentinel.TOKEN

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
            value = getattr(self, f.name)
            if value is not Sentinel.TOKEN:
                result[f.name] = value
        return result


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool = field(compare=False)
    description: Optional[str] = field(compare=False)

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name if self.domain_data is not None else None
