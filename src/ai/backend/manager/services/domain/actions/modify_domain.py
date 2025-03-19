from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.services.domain.base import DomainAction


@dataclass
class ModifyDomainAction(DomainAction):
    _name: str
    _new_name: Optional[str]
    _description: Optional[str]
    _is_active: Optional[bool]
    _total_resource_slots: Optional[ResourceSlot]
    _allowed_vfolder_hosts: Optional[dict[str, str]]
    _allowed_docker_registries: Optional[list[str]]
    _integration_id: Optional[str]

    def __init__(
        self,
        name: str,
        new_name: Optional[str],
        description: Optional[str],
        is_active: Optional[bool],
        total_resource_slots: Optional[ResourceSlot],
        allowed_vfolder_hosts: Optional[dict[str, str]],
        allowed_docker_registries: Optional[list[str]],
        integration_id: Optional[str],
    ) -> None:
        super().__init__()
        self._name = name
        self._new_name = new_name
        self._description = description
        self._is_active = is_active
        self._total_resource_slots = total_resource_slots
        self._allowed_vfolder_hosts = allowed_vfolder_hosts
        self._allowed_docker_registries = allowed_docker_registries
        self._integration_id = integration_id

    @override
    def entity_id(self) -> str:
        return self._name

    @override
    def operation_type(self) -> str:
        return "modify"

    @property
    def name(self) -> str:
        return self._name

    @property
    def new_name(self) -> Optional[str]:
        return self._new_name

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def is_active(self) -> Optional[bool]:
        return self._is_active

    @property
    def total_resource_slots(self) -> Optional[ResourceSlot]:
        return self._total_resource_slots

    @property
    def allowed_vfolder_hosts(self) -> Optional[dict[str, str]]:
        return self._allowed_vfolder_hosts

    @property
    def allowed_docker_registries(self) -> Optional[list[str]]:
        return self._allowed_docker_registries

    @property
    def integration_id(self) -> Optional[str]:
        return self._integration_id


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    _domain: Optional[DomainRow]
    _status: str
    _description: Optional[str]

    def __init__(
        self, domain_row: Optional[DomainRow], status: str, description: Optional[str]
    ) -> None:
        self._domain = domain_row
        self._status = status
        self._description = description

    @override
    def entity_id(self) -> str:
        return self._domain.name if self._domain is not None else ""

    @override
    def status(self) -> str:
        return self._status

    @override
    def description(self) -> Optional[str]:
        return self._description

    @property
    def domain_row(self) -> Optional[DomainRow]:
        return self._domain
