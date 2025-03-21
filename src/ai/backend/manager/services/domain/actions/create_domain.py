from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.services.domain.base import DomainAction


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
    def entity_id(self):
        return self.name

    @override
    def operation_type(self):
        return "create"

    def get_insert_data(self):
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
    domain_row: Optional[DomainRow]
    status: str
    description: Optional[str]

    def __init__(self, domain_row: Optional[DomainRow], status: str, description: Optional[str]):
        self.domain_row = domain_row
        self.status = status
        self.description = description

    @override
    def entity_id(self):
        return self.domain_row.name

    @property
    def ok(self):
        return self.status == "success"
