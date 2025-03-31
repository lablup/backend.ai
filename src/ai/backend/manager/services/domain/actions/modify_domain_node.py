from dataclasses import dataclass, fields
from typing import Any, Optional, override

from ai.backend.common.types import Sentinel
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, UserInfo


@dataclass
class ModifyDomainNodeAction(DomainAction):
    name: str
    user_info: UserInfo
    description: Optional[str] | Sentinel = Sentinel.TOKEN
    is_active: Optional[bool] | Sentinel = Sentinel.TOKEN
    total_resource_slots: Optional[dict[str, str]] | Sentinel = Sentinel.TOKEN
    allowed_vfolder_hosts: Optional[dict[str, str]] | Sentinel = Sentinel.TOKEN
    allowed_docker_registries: Optional[list[str]] | Sentinel = Sentinel.TOKEN
    integration_id: Optional[str] | Sentinel = Sentinel.TOKEN
    dotfiles: Optional[bytes] | Sentinel = Sentinel.TOKEN
    sgroups_to_add: Optional[list[str]] | Sentinel = Sentinel.TOKEN
    sgroups_to_remove: Optional[list[str]] | Sentinel = Sentinel.TOKEN
    client_mutation_id: Optional[str] | Sentinel = Sentinel.TOKEN

    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "modify"

    def get_modified_fields(self) -> dict[str, Any]:
        exclude_fields = [
            "name",
            "user_info",
            "sgroups_to_add",
            "sgroups_to_remove",
            "client_mutation_id",
        ]
        result = {}
        for f in fields(self):
            if f.name in exclude_fields:
                continue
            value = getattr(self, f.name)
            if value is not Sentinel.TOKEN:
                result[f.name] = value
        return result

    def get_sgroups_to_add_as_set(self) -> Optional[set[str]] | Sentinel:
        if isinstance(self.sgroups_to_add, list):
            return set(self.sgroups_to_add)
        return self.sgroups_to_add

    def get_sgroups_to_remove_as_set(self) -> Optional[set[str]] | Sentinel:
        if isinstance(self.sgroups_to_remove, list):
            return set(self.sgroups_to_remove)
        return self.sgroups_to_remove

    @property
    def has_sgroups_to_add(self) -> bool:
        return self.sgroups_to_add not in (None, Sentinel.TOKEN)

    @property
    def has_sgroups_to_remove(self) -> bool:
        return self.sgroups_to_remove not in (None, Sentinel.TOKEN)


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool
    description: Optional[str]

    @override
    def entity_id(self):
        return self.domain_data.name if self.domain_data is not None else None
