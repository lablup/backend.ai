"""CreatorSpec implementations for user entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, override

from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.repositories.base.creator import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.models.hasher.types import PasswordInfo


@dataclass
class UserCreatorSpec(CreatorSpec[UserRow]):
    """CreatorSpec for user accounts."""

    email: str
    username: str
    password: PasswordInfo
    need_password_change: bool
    domain_name: str
    full_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[UserStatus] = None
    role: Optional[str] = None
    allowed_client_ip: Optional[list[str]] = None
    totp_activated: Optional[bool] = None
    resource_policy: Optional[str] = None
    sudo_session_enabled: Optional[bool] = None
    container_uid: Optional[int] = None
    container_main_gid: Optional[int] = None
    container_gids: Optional[list[int]] = None

    @override
    def build_row(self) -> UserRow:
        # Determine status from is_active if status is None
        status = UserStatus.ACTIVE
        if self.status is None and self.is_active is not None:
            status = UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE
        elif self.status is not None:
            status = self.status
        else:
            status = UserStatus.BEFORE_VERIFICATION

        return UserRow(
            username=self.username,
            email=self.email,
            password=self.password,
            need_password_change=self.need_password_change
            if self.need_password_change is not None
            else False,
            full_name=self.full_name,
            description=self.description,
            status=status,
            domain_name=self.domain_name,
            role=self.role if self.role is not None else UserRole.USER,
            resource_policy=self.resource_policy if self.resource_policy is not None else "default",
            allowed_client_ip=self.allowed_client_ip,
            totp_activated=self.totp_activated if self.totp_activated is not None else False,
            sudo_session_enabled=self.sudo_session_enabled
            if self.sudo_session_enabled is not None
            else False,
            container_uid=self.container_uid,
            container_main_gid=self.container_main_gid,
            container_gids=self.container_gids,
        )
