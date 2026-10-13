from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field, field_validator

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.types import ReadableCIDR
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.models.user.upserters import UserUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class UserSeed(SeedItem):
    """One ``users`` row. ``password`` is the plaintext. Its keypairs, projects, roles and
    personal project are not written by this kind."""

    id: UserID
    domain_id: DomainID
    email: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1)
    need_password_change: bool = False
    full_name: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    status: UserStatus = UserStatus.ACTIVE
    status_info: str | None = None
    role: UserRole = UserRole.USER
    resource_policy: str = Field(min_length=1, max_length=256)
    allowed_client_ip: list[str] | None = None
    sudo_session_enabled: bool = False
    container_uid: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)
    container_main_gid: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)
    container_gids: list[int] | None = None

    @field_validator("allowed_client_ip")
    @classmethod
    def _readable_cidrs(cls, value: list[str] | None) -> list[str] | None:
        """The rule ``users.allowed_client_ip`` checks on bind, so the file fails
        ``seed check``."""
        for address in value or []:
            try:
                ReadableCIDR(address)
            except InvalidIpAddressValue as e:
                raise ValueError(f"{address!r} is not an IP address or network") from e
        return value

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=UserUpserter(
                id=self.id,
                domain_id=self.domain_id,
                email=self.email,
                username=self.username,
                password=PasswordInfo(
                    password=self.password,
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=self.need_password_change,
                full_name=self.full_name,
                description=self.description,
                status=self.status,
                status_info=self.status_info,
                role=self.role,
                resource_policy=self.resource_policy,
                allowed_client_ip=self.allowed_client_ip,
                sudo_session_enabled=self.sudo_session_enabled,
                container_uid=self.container_uid,
                container_main_gid=self.container_main_gid,
                container_gids=self.container_gids,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[UserSeed]]) -> list[SeedRejection]:
        return []
