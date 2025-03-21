from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.services.domain.base import DomainAction


@dataclass
class ModifyDomainAction(DomainAction):
    name: str
    new_name: Optional[str]
    description: Optional[str]
    is_active: Optional[bool]
    total_resource_slots: Optional[ResourceSlot]
    allowed_vfolder_hosts: Optional[dict[str, str]]
    allowed_docker_registries: Optional[list[str]]
    integration_id: Optional[str]

    @override
    def entity_id(self) -> str:
        return self.name

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    domain_row: Optional[DomainRow]
    status: str
    description: Optional[str]

    @override
    def entity_id(self) -> str:
        return self.domain_row.name if self.domain_row is not None else ""

    @property
    def ok(self) -> bool:
        return self.status == "success"
