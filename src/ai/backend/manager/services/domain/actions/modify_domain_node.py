import uuid
from dataclasses import dataclass
from typing import Optional, cast

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.gql_relay import ResolvedGlobalID
from ai.backend.manager.services.domain.base import DomainAction, UserInfo


@dataclass
class ModifyDomainNodeAction(DomainAction):
    _id: uuid.UUID | str
    _description: Optional[str]
    _is_active: Optional[bool]
    _total_resource_slots: Optional[dict[str, str]]
    _allowed_vfolder_hosts: Optional[dict[str, str]]
    _allowed_docker_registries: Optional[list[str]]
    _integration_id: Optional[str]
    _dotfiles: Optional[bytes]
    _sgroups_to_add: Optional[list[str]]
    _sgroups_to_remove: Optional[list[str]]
    _client_mutation_id: Optional[str]
    _user_info: UserInfo

    def __init__(
        self,
        id: uuid.UUID | str,
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
        self._id = id
        self._description = description
        self._is_active = is_active
        self._total_resource_slots = total_resource_slots
        self._allowed_vfolder_hosts = allowed_vfolder_hosts
        self._allowed_docker_registries = allowed_docker_registries
        self._integration_id = integration_id
        self._dotfiles = dotfiles
        self._sgroups_to_add = sgroups_to_add
        self._sgroups_to_remove = sgroups_to_remove
        self._client_mutation_id = client_mutation_id
        self._user_info = user_info

    def entity_id(self):
        return self._id

    def operation_type(self):
        return "modify"

    @property
    def domain_name(self):
        _, name = cast(ResolvedGlobalID, self.id)
        return name

    @property
    def user_info(self):
        return self._user_info


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    _domain_row: DomainRow
    _status: str
    _description: Optional[str]

    def __init__(self, domain_row: DomainRow, status: str, description: Optional[str]):
        self._domain_row = domain_row
        self._status = status
        self._description = description

    def entity_id(self):
        return self._domain_row.name

    def status(self):
        return self._status

    def description(self):
        return self._description

    @property
    def domain_row(self):
        return self._domain_row
