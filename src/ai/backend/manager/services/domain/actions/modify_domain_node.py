from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, UserInfo


@dataclass
class ModifyDomainNodeAction(DomainAction):
    name: str
    user_info: UserInfo
    description: Optional[str] = None
    is_active: Optional[bool] = None
    total_resource_slots: Optional[dict[str, str]] = None
    allowed_vfolder_hosts: Optional[dict[str, str]] = None
    allowed_docker_registries: Optional[list[str]] = None
    integration_id: Optional[str] = None
    dotfiles: Optional[bytes] = None
    sgroups_to_add: Optional[list[str]] = None
    sgroups_to_remove: Optional[list[str]] = None
    client_mutation_id: Optional[str] = None

    def entity_id(self):
        return self._id

    def operation_type(self):
        return "modify"

    def get_update_values_as_dict(self):
        base_dict = {
            "description": self.description,
            "is_active": self.is_active,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "allowed_docker_registries": self.allowed_docker_registries,
            "integration_id": self.integration_id,
            "dotfiles": self.dotfiles,
        }

        return {k: v for k, v in base_dict.items() if v is not None}


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    status: str
    description: Optional[str]

    @override
    def entity_id(self):
        return self.domain_row.name
