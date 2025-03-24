from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData


@dataclass
class ModifyDomainAction(DomainAction):
    name: str
    new_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    total_resource_slots: Optional[ResourceSlot] = None
    allowed_vfolder_hosts: Optional[dict[str, str]] = None
    allowed_docker_registries: Optional[list[str]] = None
    integration_id: Optional[str] = None

    @override
    def entity_id(self) -> str:
        return self.name

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    status: str
    description: Optional[str]

    @override
    def entity_id(self) -> str:
        return self.domain_data.name if self.domain_data is not None else ""

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def __eq__(self, other):
        return self.domain_data == other.domain_data
