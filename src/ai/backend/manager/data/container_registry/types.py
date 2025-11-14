import uuid
from dataclasses import dataclass
from typing import Any, Optional

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, TriState


@dataclass
class ContainerRegistryData:
    id: uuid.UUID
    url: str
    registry_name: str
    type: ContainerRegistryType
    project: str
    username: Optional[str]
    password: Optional[str]
    ssl_verify: Optional[bool]
    is_global: Optional[bool]
    # TODO: Add proper type
    extra: Optional[dict[str, Any]]


@dataclass
class ContainerRegistryCreator(Creator):
    url: str
    type: ContainerRegistryType
    registry_name: str
    is_global: Optional[bool]
    project: str
    username: Optional[str]
    password: Optional[str]
    ssl_verify: Optional[bool]
    extra: Optional[dict[str, Any]]
    allowed_groups: Optional[AllowedGroupsModel]

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "type": self.type.value,
            "registry_name": self.registry_name,
            "is_global": self.is_global,
            "project": self.project,
            "username": self.username,
            "password": self.password,
            "ssl_verify": self.ssl_verify,
            "extra": self.extra,
        }


@dataclass
class ContainerRegistryModifier(PartialModifier):
    url: OptionalState[str]
    type: OptionalState[ContainerRegistryType]
    registry_name: OptionalState[str]
    is_global: TriState[bool]
    project: OptionalState[str]
    username: TriState[str]
    password: TriState[str]
    ssl_verify: TriState[bool]
    extra: TriState[dict[str, Any]]
    allowed_groups: TriState[AllowedGroupsModel]

    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.url.update_dict(to_update, "url")
        self.type.update_dict(to_update, "type")
        self.registry_name.update_dict(to_update, "registry_name")
        self.is_global.update_dict(to_update, "is_global")
        self.project.update_dict(to_update, "project")
        self.username.update_dict(to_update, "username")
        self.password.update_dict(to_update, "password")
        self.ssl_verify.update_dict(to_update, "ssl_verify")
        self.extra.update_dict(to_update, "extra")
        return to_update
