from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, UserInfo


@dataclass
class CreateDomainNodeAction(DomainAction):
    name: str
    user_info: UserInfo
    description: Optional[str]
    is_active: Optional[bool]
    total_resource_slots: Optional[dict[str, str]]
    allowed_vfolder_hosts: Optional[dict[str, str]]
    allowed_docker_registries: Optional[list[str]]
    integration_id: Optional[str]
    dotfiles: Optional[bytes]
    scaling_groups: Optional[list[str]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"

    def get_insertion_data(self) -> dict[str, Any]:
        result: dict[str, Any] = {"name": self.name}

        optional_fields = [
            "description",
            "is_active",
            "total_resource_slots",
            "allowed_vfolder_hosts",
            "allowed_docker_registries",
            "integration_id",
            "dotfiles",
            "scaling_groups",
        ]

        for field_name in optional_fields:
            field_value = getattr(self, field_name)
            result[field_name] = field_value

        return result


@dataclass
class CreateDomainNodeActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool
    description: str

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name if self.domain_data is not None else None
