from __future__ import annotations

import enum

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.data.entity.types import EntityIdentifier, GlobalEntityType
from ai.backend.common.exception import UnreachableError

__all__ = (
    "SystemSessionEnvironScopeType",
    "SystemSessionEnvironSourceKind",
    "SystemSessionEnvironValueSource",
)


class SystemSessionEnvironScopeType(enum.StrEnum):
    PUBLIC = "public"
    DOMAIN = "domain"
    PROJECT = "project"

    @classmethod
    def of_owner(cls, owner: EntityIdentifier) -> SystemSessionEnvironScopeType:
        match owner:
            case _ if owner.entity_type() == GlobalEntityType():
                return cls.PUBLIC
            case _ if owner.entity_type() == DomainEntityType():
                return cls.DOMAIN
            case _ if owner.entity_type() == ProjectEntityType():
                return cls.PROJECT
            case _:
                raise UnreachableError(
                    f"No system session environ scope is owned by a {owner.entity_type()}"
                )

    def to_owner(self, scope_id: SystemSessionEnvironScopeID) -> EntityIdentifier:
        match self:
            case SystemSessionEnvironScopeType.PUBLIC:
                return GlobalEntityID(scope_id)
            case SystemSessionEnvironScopeType.DOMAIN:
                return DomainID(scope_id)
            case SystemSessionEnvironScopeType.PROJECT:
                return ProjectID(scope_id)


class SystemSessionEnvironSourceKind(enum.StrEnum):
    """``required`` values win over the session's own environ; ``optional`` ones lose to it."""

    REQUIRED = "required"
    OPTIONAL = "optional"


class SystemSessionEnvironValueSource(enum.StrEnum):
    SESSION_ID = "session_id"
    SESSION_NAME = "session_name"
    CLUSTER_SIZE = "cluster_size"
    CLUSTER_REPLICAS = "cluster_replicas"
    CLUSTER_HOSTS = "cluster_hosts"
    PREOPEN_PORTS = "preopen_ports"
    USER_UUID = "user_uuid"
    USER_EMAIL = "user_email"
    USER_NAME = "user_name"
    ACCESS_KEY = "access_key"

    def kind(self) -> SystemSessionEnvironSourceKind:
        if self in [
            SystemSessionEnvironValueSource.USER_UUID,
            SystemSessionEnvironValueSource.USER_EMAIL,
            SystemSessionEnvironValueSource.USER_NAME,
            SystemSessionEnvironValueSource.ACCESS_KEY,
        ]:
            return SystemSessionEnvironSourceKind.OPTIONAL
        return SystemSessionEnvironSourceKind.REQUIRED
