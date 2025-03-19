from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.services.vfolder.base import DomainAction


@dataclass
class ModifyDomainAction(DomainAction):
    _name: str
    _description: Optional[str]
    _is_active: Optional[bool]
    _total_resource_slots: Optional[dict[str, str]]
    _allowed_vfolder_hosts: Optional[dict[str, str]]
    _allowed_docker_registries: Optional[list[str]]
    _integration_id: Optional[str]

    @override
    def entity_id(self) -> str:
        return self._name

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    _domain: DomainRow
    _status: str
    _description: Optional[str]

    @override
    def entity_id(self) -> str:
        return self._domain.name

    @override
    def status(self) -> str:
        return self._status
