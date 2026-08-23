"""Creator specs for the users table."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    NotNullViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.user import UserCreationBadRequest
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.creator import RoleManagedEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.user.row import UserRole, UserRow

if TYPE_CHECKING:
    from ai.backend.manager.models.hasher.types import PasswordInfo


@dataclass
class UserCreator(RoleManagedEntityCreator[UserRow, UserData]):
    """Registers a user in a domain."""

    email: str
    username: str
    password: PasswordInfo
    need_password_change: bool
    domain_id: DomainID
    full_name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    status: UserStatus | None = None
    status_info: str | None = None
    role: str | None = None
    allowed_client_ip: list[str] | None = None
    totp_activated: bool | None = None
    resource_policy: str | None = None
    sudo_session_enabled: bool | None = None
    container_uid: int | None = None
    container_main_gid: int | None = None
    container_gids: list[int] | None = None
    integration_name: str | None = None

    @override
    def entity_id(self, row: UserRow) -> EntityIdentifier:
        return UserID(row.uuid)

    @override
    def member_of(self, row: UserRow) -> Collection[EntityIdentifier]:
        return (self.domain_id,)

    @override
    def template_value(self, row: UserRow) -> ScopeTemplateValue:
        return ScopeTemplateValue(id=row.uuid, name=row.username, type=USER_SCOPE_TYPE)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=UserCreationBadRequest(
                    "Failed to create user due to database constraint violation"
                ),
            ),
            # The name column is filled from the id; an unknown id leaves it NULL.
            IntegrityErrorCheck(
                violation_type=NotNullViolationError,
                error=UserCreationBadRequest(f"Domain '{self.domain_id}' does not exist."),
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=UserCreationBadRequest(f"Domain '{self.domain_id}' does not exist."),
            ),
        )

    @override
    def build_row(self) -> UserRow:
        return UserRow(
            username=self.username,
            email=self.email,
            password=self.password,
            need_password_change=self.need_password_change
            if self.need_password_change is not None
            else False,
            full_name=self.full_name,
            description=self.description,
            status=self._status(),
            status_info=self.status_info,
            domain_id=self.domain_id,
            # Deprecated column kept in step with the id, computed inside the INSERT.
            domain_name=sa.select(DomainRow.name)
            .where(DomainRow.id == self.domain_id)
            .scalar_subquery(),
            role=UserRole(self.role) if self.role is not None else UserRole.USER,
            resource_policy=self.resource_policy if self.resource_policy is not None else "default",
            allowed_client_ip=self.allowed_client_ip,
            totp_activated=self.totp_activated if self.totp_activated is not None else False,
            sudo_session_enabled=self.sudo_session_enabled
            if self.sudo_session_enabled is not None
            else False,
            container_uid=self.container_uid,
            container_main_gid=self.container_main_gid,
            container_gids=self.container_gids,
            integration_id=self.integration_name,  # DB column is integration_id
        )

    @override
    def to_data(self, row: UserRow) -> UserData:
        return row.to_data()

    def _status(self) -> UserStatus:
        """The explicit status, else the one ``is_active`` implies, else unverified."""
        if self.status is not None:
            return self.status
        if self.is_active is not None:
            return UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE
        return UserStatus.BEFORE_VERIFICATION
