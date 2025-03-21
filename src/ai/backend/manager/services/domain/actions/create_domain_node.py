from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.services.domain.base import DomainAction, UserInfo


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


@dataclass
class CreateDomainNodeActionResult(BaseActionResult):
    domain_row: DomainRow
    status: str
    description: Optional[str]

    def __init__(self, domain_row: DomainRow, status: str, description: Optional[str]):
        self.domain_row = domain_row
        self.status = status
        self.description = description

    @override
    def entity_id(self):
        return self.domain_row.name
