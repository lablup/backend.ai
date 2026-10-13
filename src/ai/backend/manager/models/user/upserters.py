"""Upsert specs for the users table."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.user.row import UserRole, UserRow
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields

__all__ = ("UserUpserter",)


@dataclass
class UserUpserter(EntityUpserter[UserRow, UserData]):
    """Write a user under its stated uuid, created in its domain and `global` as the user
    creator does. Conflict key: uuid. The domain and the password are written on insert
    only; the password column hashes ``password`` on bind."""

    id: UserID
    domain_id: DomainID
    email: str
    username: str
    password: PasswordInfo
    need_password_change: bool
    full_name: str | None
    description: str | None
    status: UserStatus
    status_info: str | None
    role: UserRole
    resource_policy: str
    allowed_client_ip: list[str] | None
    sudo_session_enabled: bool
    container_uid: int | None
    container_main_gid: int | None
    container_gids: list[int] | None

    @override
    def entity_id(self, row: UserRow) -> UserID:
        return UserID(row.uuid)

    @override
    def created_in(self, row: UserRow) -> Collection[EntityIdentifier]:
        """The row's domain: an overwrite stating another one leaves the user where it is."""
        return (DomainID(row.domain_id), global_entity_id(GlobalEntityName.GLOBAL))

    @override
    def row_class(self) -> type[UserRow]:
        return UserRow

    @override
    def index_elements(self) -> list[str]:
        return ["uuid"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        """A domain id naming no row leaves ``domain_name`` NULL, which the column
        refuses."""
        return {
            "uuid": self.id,
            "domain_id": self.domain_id,
            "domain_name": sa.select(DomainRow.name)
            .where(DomainRow.id == self.domain_id)
            .scalar_subquery(),
            "password": self.password,
            **self._values(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "username": self.username,
            "need_password_change": self.need_password_change,
            "full_name": self.full_name,
            "description": self.description,
            "status": self.status,
            "status_info": self.status_info,
            "role": self.role,
            "resource_policy": self.resource_policy,
            "allowed_client_ip": self.allowed_client_ip,
            "sudo_session_enabled": self.sudo_session_enabled,
            "container_uid": self.container_uid,
            "container_main_gid": self.container_main_gid,
            "container_gids": self.container_gids,
        }

    @override
    def to_data(self, row: UserRow) -> UserData:
        return UserSearchableFields.own.to_data(row)
