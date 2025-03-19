from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.services.vfolder.base import DomainAction


@dataclass
class CreateDomainAction(DomainAction):
    _name: str
    _description: Optional[str]
    _is_active: Optional[bool]
    _total_resource_slots: Optional[dict[str, str]]
    _allowed_vfolder_hosts: Optional[dict[str, str]]
    _allowed_docker_registries: Optional[list[str]]
    _integration_id: Optional[str]

    def __init__(
        self,
        name: str,
        description: Optional[str],
        is_active: Optional[bool],
        total_resource_slots: Optional[dict[str, str]],
        allowed_vfolder_hosts: Optional[dict[str, str]],
        allowed_docker_registries: Optional[list[str]],
        integration_id: Optional[str],
    ) -> None:
        super().__init__()
        self._name = name
        self._description = description
        self._is_active = is_active
        self._total_resource_slots = total_resource_slots
        self._allowed_vfolder_hosts = allowed_vfolder_hosts
        self._allowed_docker_registries = allowed_docker_registries
        self._integration_id = integration_id

    @override
    def entity_id(self):
        return self._name

    @override
    def operation_type(self):
        return "create"

    @override
    def get_insert_data(self):
        return {
            "name": self._name,
            "description": self._description,
            "is_active": self._is_active,
            "total_resource_slots": ResourceSlot.from_user_input(self._total_resource_slots, None),
            "allowed_vfolder_hosts": self._allowed_vfolder_hosts,
            "allowed_docker_registries": self._allowed_docker_registries,
            "integration_id": self._integration_id,
        }

    @property
    def domain_name(self):
        return self._name


@dataclass
class CreateDomainActionResult(BaseActionResult):
    _domain_row: Optional[DomainRow]
    _status: str
    _description: Optional[str]

    def __init__(self, domain_row: Optional[DomainRow], status: str, description: Optional[str]):
        self._domain_row = domain_row
        self._status = status
        self._description = description

    @override
    def entity_id(self):
        return self._domain_row.name

    @override
    def status(self):
        return self._status

    @override
    def description(self):
        return self._description

    @property
    def domain_row(self):
        return self._domain_row
