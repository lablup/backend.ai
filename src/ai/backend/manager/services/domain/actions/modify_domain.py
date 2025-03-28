from dataclasses import dataclass
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
    def entity_id(self) -> str:
        return self.domain_name

    @override
    def operation_type(self) -> str:
        return "modify"

    def get_modified_fields(self) -> dict[str, Any]:
        return {
            k: v for k, v in self.__dict__.items() if v is not Sentinel.TOKEN and k != "domain_name"
        }


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool
    description: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name if self.domain_data is not None else None

    def __eq__(self, other):
        return self.domain_data == other.domain_data
