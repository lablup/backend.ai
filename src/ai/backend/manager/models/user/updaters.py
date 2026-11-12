"""Update specs for the users table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.auth.password import PasswordInfo
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.user import (
    UserDeleted,
    UserModificationBadRequest,
    UserPurgeInProgress,
)
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class UserUpdater(GuardedDataUpdater[UserRow, UserData]):
    """Edits a user account; refuses a deleted user and one a purge is working through.

    ``status`` takes ACTIVE or INACTIVE only. ``group_ids`` is not a column; the write
    path syncs it separately from ``build_values()``.
    """

    user_id: UserID
    username: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    password: OptionalState[PasswordInfo] = field(default_factory=OptionalState[PasswordInfo].nop)
    need_password_change: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    full_name: TriState[str] = field(default_factory=TriState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    status: OptionalState[UserStatus] = field(default_factory=OptionalState[UserStatus].nop)
    domain_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    role: OptionalState[UserRole] = field(default_factory=OptionalState[UserRole].nop)
    allowed_client_ip: TriState[list[str]] = field(default_factory=TriState[list[str]].nop)
    totp_activated: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    sudo_session_enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    container_uid: TriState[int] = field(default_factory=TriState[int].nop)
    container_main_gid: TriState[int] = field(default_factory=TriState[int].nop)
    container_gids: TriState[list[int]] = field(default_factory=TriState[list[int]].nop)
    integration_name: TriState[str] = field(default_factory=TriState[str].nop)
    group_ids: OptionalState[list[str]] = field(default_factory=OptionalState[list[str]].nop)

    def __post_init__(self) -> None:
        status = self.status.optional_value()
        if status is not None and status not in (UserStatus.ACTIVE, UserStatus.INACTIVE):
            raise UserModificationBadRequest(
                f"Status '{status}' cannot be set by an update; use delete or restore."
            )

    @property
    @override
    def row_class(self) -> type[UserRow]:
        return UserRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return UserRow.uuid

    @override
    def target_id_value(self) -> UserID:
        return self.user_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=UserSearchableFields.own.status.filter.not_in(
                    UserStatus.purge_in_progress()
                ),
                error=UserPurgeInProgress(f"User is being purged: {self.user_id}"),
            ),
            GuardCheck(
                condition=UserSearchableFields.own.status.filter.not_equals(UserStatus.DELETED),
                error=UserDeleted(f"User is deleted: {self.user_id}"),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.username.update_dict(to_update, "username")
        # Can't remove password - special handling
        password = self.password.optional_value()
        if password is not None:
            to_update["password"] = password
        self.need_password_change.update_dict(to_update, "need_password_change")
        self.full_name.update_dict(to_update, "full_name")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.domain_name.update_dict(to_update, "domain_name")
        self.role.update_dict(to_update, "role")
        self.allowed_client_ip.update_dict(to_update, "allowed_client_ip")
        self.totp_activated.update_dict(to_update, "totp_activated")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.sudo_session_enabled.update_dict(to_update, "sudo_session_enabled")
        self.container_uid.update_dict(to_update, "container_uid")
        self.container_main_gid.update_dict(to_update, "container_main_gid")
        self.container_gids.update_dict(to_update, "container_gids")
        # Field is named integration_name above model layer; DB column remains integration_id.
        self.integration_name.update_dict(to_update, "integration_id")
        # Set status based on is_active if not explicitly set
        status = self.status.optional_value()
        if status is not None:
            to_update["status"] = status
        else:
            is_active = self.is_active.optional_value()
            if is_active is not None:
                to_update["status"] = UserStatus.ACTIVE if is_active else UserStatus.INACTIVE
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: UserRow) -> UserData:
        return UserSearchableFields.own.to_data(row)

    @property
    def group_ids_value(self) -> list[str] | None:
        """Helper property for group_ids access."""
        return self.group_ids.optional_value()
