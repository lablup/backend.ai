from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.services.domain.base import DomainAction, UserInfo


@dataclass
class ModifyDomainNodeAction(DomainAction):
    name: str
    description: Optional[str]
    is_active: Optional[bool]
    total_resource_slots: Optional[dict[str, str]]
    allowed_vfolder_hosts: Optional[dict[str, str]]
    allowed_docker_registries: Optional[list[str]]
    integration_id: Optional[str]
    dotfiles: Optional[bytes]
    sgroups_to_add: Optional[list[str]]
    sgroups_to_remove: Optional[list[str]]
    client_mutation_id: Optional[str]
    user_info: UserInfo

    def __init__(
        self,
        name: str,
        description: Optional[str],
        is_active: Optional[bool],
        total_resource_slots: Optional[dict[str, str]],
        allowed_vfolder_hosts: Optional[dict[str, str]],
        allowed_docker_registries: Optional[list[str]],
        integration_id: Optional[str],
        dotfiles: Optional[bytes],
        sgroups_to_add: Optional[list[str]],
        sgroups_to_remove: Optional[list[str]],
        client_mutation_id: Optional[str],
        user_info: UserInfo,
    ) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.is_active = is_active
        self.total_resource_slots = total_resource_slots
        self.allowed_vfolder_hosts = allowed_vfolder_hosts
        self.allowed_docker_registries = allowed_docker_registries
        self.integration_id = integration_id
        self.dotfiles = dotfiles
        self.sgroups_to_add = sgroups_to_add
        self.sgroups_to_remove = sgroups_to_remove
        self.client_mutation_id = client_mutation_id
        self.user_info = user_info

    def entity_id(self):
        return self._id

    def operation_type(self):
        return "modify"


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    domain_row: DomainRow
    status: str
    description: Optional[str]

    @override
    def entity_id(self):
        return self.domain_row.name
