from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import override

from pydantic import ConfigDict, Field, field_validator

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.types import AccessKey, BackendAISchema, ReadableCIDR
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.secret import InvalidEncryptedSecretFormat
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair.upserters import KeypairUpserter
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.models.user.upserters import UserUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class UserKeypairSeed(BackendAISchema):
    """One ``keypairs`` row of the user. ``secret_key`` is the plaintext."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    access_key: AccessKey = Field(min_length=1, max_length=20)
    secret_key: str = Field(min_length=1)
    is_active: bool = True
    is_admin: bool = False
    is_default: bool = False
    resource_policy_id: KeyPairResourcePolicyUUID
    rate_limit: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)
    ssh_public_key: str | None = None
    ssh_private_key: str | None = None

    @field_validator("secret_key")
    @classmethod
    def _plaintext(cls, value: str) -> str:
        """The rule ``SecretValue`` checks on build, so the file fails ``seed check``."""
        try:
            SecretValue(value)
        except InvalidEncryptedSecretFormat as e:
            raise ValueError(str(e)) from e
        return value

    def upserter(self) -> KeypairUpserter:
        return KeypairUpserter(
            access_key=self.access_key,
            secret_key=self.secret_key,
            is_active=self.is_active,
            is_admin=self.is_admin,
            is_default=self.is_default,
            resource_policy_id=self.resource_policy_id,
            rate_limit=self.rate_limit,
            ssh_public_key=self.ssh_public_key,
            ssh_private_key=self.ssh_private_key,
        )


class UserSeed(SeedItem):
    """One ``users`` row and its ``keypairs`` rows. ``password`` is the plaintext. Its
    projects, roles and personal project are not written by this kind."""

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
    resource_policy_id: UserResourcePolicyUUID
    allowed_client_ip: list[str] | None = None
    sudo_session_enabled: bool = False
    container_uid: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)
    container_main_gid: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)
    container_gids: list[int] | None = None
    keypairs: list[UserKeypairSeed] = []

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
        """The user, and its keypairs with the default one last: an overwrite moving the
        default clears the old one before the partial unique index sees two."""
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
                resource_policy_id=self.resource_policy_id,
                allowed_client_ip=self.allowed_client_ip,
                sudo_session_enabled=self.sudo_session_enabled,
                container_uid=self.container_uid,
                container_main_gid=self.container_main_gid,
                container_gids=self.container_gids,
            ),
            field_upserters=[
                keypair.upserter()
                for keypair in sorted(self.keypairs, key=lambda keypair: keypair.is_default)
            ],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        """The rules the create API applies to the container ids and the default keypair."""
        failures = [
            f"{name} {value} is negative"
            for name, value in (
                ("container_uid", self.container_uid),
                ("container_main_gid", self.container_main_gid),
                *(("container_gids", gid) for gid in self.container_gids or []),
            )
            if value is not None and value < 0
        ]
        failures.extend(
            f"default keypair {keypair.access_key} is inactive"
            for keypair in self.keypairs
            if keypair.is_default and not keypair.is_active
        )
        return failures

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[UserSeed]]) -> list[SeedRejection]:
        """The files stating an access key more than once: the keypair upsert keys on it,
        so a second statement would rewrite the first instead of failing."""
        sources_by_key: dict[str, list[str]] = defaultdict(list)
        for file in files:
            for seed in file.items:
                for keypair in seed.keypairs:
                    sources_by_key[keypair.access_key].append(file.source)
        return [
            SeedRejection(source, f"keypair {key} is stated {len(sources)} times")
            for key, sources in sorted(sources_by_key.items())
            if len(sources) > 1
            for source in sorted(set(sources))
        ]
