from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, UserInfo


@dataclass
class CreateDomainNodeAction(DomainAction):
    name: str
    description: Optional[str]
    scaling_groups: Optional[list[str]]
    user_info: UserInfo
    is_active: Optional[bool] = True
    total_resource_slots: Optional[dict[str, str]] = field(default_factory=dict)
    allowed_vfolder_hosts: Optional[dict[str, str]] = field(default_factory=dict)
    allowed_docker_registries: Optional[list[str]] = field(default_factory=list)
    integration_id: Optional[str] = None
    dotfiles: Optional[bytes] = b"\x90"

    @override
    def entity_id(self):
        return self.name

    @override
    def operation_type(self):
        return "create"

    def get_insertion_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "allowed_docker_registries": self.allowed_docker_registries,
            "integration_id": self.integration_id,
            "dotfiles": self.dotfiles,
        }


@dataclass
class CreateDomainNodeActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    status: str
    description: Optional[str]

    @override
    def entity_id(self):
        return self.domain_row.name
