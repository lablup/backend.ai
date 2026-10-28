from __future__ import annotations

import ipaddress
from collections.abc import Sequence
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
)

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import (
    Mapped,
    foreign,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.expression import SQLColumnExpression

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ReadableCIDR
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.model_serving.types import UserData as ModelServingUserData
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.models.base import (
    GUID,
    Base,
    EnumValueType,
    IPColumn,
)
from ai.backend.manager.models.hasher.factory import PasswordHasherFactory
from ai.backend.manager.models.hasher.types import HashInfo, PasswordColumn, PasswordInfo
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

if TYPE_CHECKING:
    from ai.backend.manager.models.domain.row import DomainRow
    from ai.backend.manager.models.keypair.row import KeyPairRow
    from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow


__all__: Sequence[str] = (
    "ACTIVE_USER_STATUSES",
    "INACTIVE_USER_STATUSES",
    "PasswordColumn",  # Re-exported from hasher/types.py
    "PasswordHashAlgorithm",
    "UserRole",  # For compatibility with existing code
    "UserRow",
    "UserStatus",  # For compatibility with existing code
    "check_credential",
    "check_credential_with_migration",
    "compare_to_hashed_password",
    "users",
)


ACTIVE_USER_STATUSES = (UserStatus.ACTIVE,)

INACTIVE_USER_STATUSES = (
    UserStatus.INACTIVE,
    UserStatus.DELETED,
    UserStatus.BEFORE_VERIFICATION,
)


# Defined for avoiding circular import
def _get_domain_join_condition() -> Any:
    from ai.backend.manager.models.domain.row import DomainRow

    return DomainRow.name == foreign(UserRow.domain_name)


def _get_resource_policy_join_condition() -> Any:
    from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow

    return UserResourcePolicyRow.name == foreign(UserRow.resource_policy)


def _get_keypairs_join_condition() -> Any:
    from ai.backend.manager.models.keypair.row import KeyPairRow

    return foreign(KeyPairRow.user) == UserRow.uuid


class UserRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "users"

    uuid: Mapped[UserID] = mapped_column(
        "uuid", GUID(UserID), primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    username: Mapped[str] = mapped_column(
        "username", sa.String(length=64), unique=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        "email", sa.String(length=64), index=True, nullable=False, unique=True
    )
    password: Mapped[str | None] = mapped_column("password", PasswordColumn(), nullable=True)
    need_password_change: Mapped[bool] = mapped_column(
        "need_password_change",
        sa.Boolean,
        server_default=sa.false(),
        default=False,
        nullable=False,
    )
    password_changed_at: Mapped[datetime] = mapped_column(
        "password_changed_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column("full_name", sa.String(length=64), nullable=True)
    description: Mapped[str | None] = mapped_column(
        "description", sa.String(length=500), nullable=True
    )
    status: Mapped[UserStatus] = mapped_column(
        "status", EnumValueType(UserStatus), default=UserStatus.BEFORE_VERIFICATION, nullable=False
    )
    status_info: Mapped[str | None] = mapped_column(
        "status_info", sa.Unicode(), nullable=True, default=sa.null()
    )
    #: Field for synchronization with external services.
    integration_id: Mapped[str | None] = mapped_column(
        "integration_id", sa.String(length=512), nullable=True
    )
    #: Deprecated: use ``domain_id``.
    domain_name: Mapped[str] = mapped_column(
        "domain_name",
        sa.String(length=64),
        sa.ForeignKey("domains.name"),
        index=True,
        nullable=False,
    )
    domain_id: Mapped[DomainID] = mapped_column(
        "domain_id",
        GUID(DomainID),
        sa.ForeignKey("domains.id"),
        index=True,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        "role", EnumValueType(UserRole), default=UserRole.USER, nullable=False
    )
    allowed_client_ip: Mapped[
        list[ReadableCIDR[ipaddress.IPv4Network | ipaddress.IPv6Network]] | None
    ] = mapped_column("allowed_client_ip", pgsql.ARRAY(IPColumn), nullable=True)
    totp_key: Mapped[str | None] = mapped_column("totp_key", sa.String(length=32), nullable=True)
    totp_activated: Mapped[bool] = mapped_column(
        "totp_activated", sa.Boolean, server_default=sa.false(), default=False, nullable=False
    )
    totp_activated_at: Mapped[datetime | None] = mapped_column(
        "totp_activated_at", sa.DateTime(timezone=True), nullable=True
    )
    resource_policy: Mapped[str] = mapped_column(
        "resource_policy",
        sa.String(length=256),
        sa.ForeignKey("user_resource_policies.name"),
        nullable=False,
    )
    sudo_session_enabled: Mapped[bool] = mapped_column(
        "sudo_session_enabled",
        sa.Boolean,
        default=False,
        nullable=False,
    )
    container_uid: Mapped[int | None] = mapped_column(
        "container_uid", sa.Integer, nullable=True, server_default=sa.null()
    )
    container_main_gid: Mapped[int | None] = mapped_column(
        "container_main_gid", sa.Integer, nullable=True, server_default=sa.null()
    )
    container_gids: Mapped[list[int] | None] = mapped_column(
        "container_gids", sa.ARRAY(sa.Integer), nullable=True, server_default=sa.null()
    )

    # Relationships
    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow", primaryjoin=_get_domain_join_condition
    )
    resource_policy_row: Mapped[UserResourcePolicyRow] = relationship(
        "UserResourcePolicyRow",
        primaryjoin=_get_resource_policy_join_condition,
    )
    keypairs: Mapped[list[KeyPairRow]] = relationship(
        "KeyPairRow",
        primaryjoin=_get_keypairs_join_condition,
        foreign_keys="KeyPairRow.user",
    )

    @classmethod
    def scope_id_expr(cls) -> SQLColumnExpression[UserID]:
        return cls.uuid

    @classmethod
    def scope_name_expr(cls) -> SQLColumnExpression[str]:
        return cls.username

    def to_model_serving_user_data(self) -> ModelServingUserData:
        return ModelServingUserData(
            uuid=self.uuid,
            email=self.email,
        )


# For compatibility
users = UserRow.__table__


def _verify_password(guess: str, hashed: str) -> bool:
    """Verify a password against a hashed password."""
    hash_info = HashInfo.from_hash_string(hashed)
    hasher = PasswordHasherFactory.get_hasher(hash_info.algorithm)
    return hasher.verify(guess, hash_info)


def compare_to_hashed_password(raw_password: str, hashed_password: str) -> bool:
    """
    Compare a raw string password value to hashed password.
    """
    return _verify_password(raw_password, hashed_password)


async def check_credential_with_migration(
    db: ExtendedAsyncSAEngine,
    domain: str,
    email: str,
    target_password_info: PasswordInfo,
) -> sa.RowMapping:
    """
    Check user credentials and optionally migrate password hash if needed.

    Args:
        db: Database engine
        domain: User's domain
        email: User's email
        target_password_info: Password configuration containing password and target hash settings

    Returns:
        User row if credentials are valid

    Raises:
        AuthorizationFailed: If user not found, password not set, or password mismatch
    """

    async with db.begin_readonly() as conn:
        result = await conn.execute(
            sa.select(users)
            .select_from(users)
            .where(
                (users.c.email == email) & (users.c.domain_name == domain),
            ),
        )
    row = result.first()
    if row is None:
        raise AuthorizationFailed("User credential mismatch.")
    if row.password is None:
        raise AuthorizationFailed("User credential mismatch.")

    try:
        if not _verify_password(target_password_info.password, row.password):
            raise AuthorizationFailed("User credential mismatch.")
    except ValueError as e:
        raise AuthorizationFailed("User credential mismatch.") from e

    # Password is valid, check if we need to migrate the hash
    current_hash_info = HashInfo.from_hash_string(row.password)
    if target_password_info.need_migration(current_hash_info):
        # Re-hash the password with the new algorithm using the provided PasswordInfo
        # Update the user's password hash asynchronously
        async with db.begin() as conn:
            await conn.execute(
                sa.update(users)
                .where((users.c.email == email) & (users.c.domain_name == domain))
                .values(password=target_password_info)
            )

    row_mapping: sa.RowMapping = row._mapping
    return row_mapping


async def check_credential(
    db: ExtendedAsyncSAEngine,
    domain: str,
    email: str,
    password: str,
) -> sa.RowMapping:
    """
    Check user credentials without migration (for signout, update password, etc.)

    Args:
        db: Database engine
        domain: User's domain
        email: User's email
        password: Plain text password to verify

    Returns:
        User row if credentials are valid

    Raises:
        AuthorizationFailed: If user not found, password not set, or password mismatch
    """

    async with db.begin_readonly() as conn:
        result = await conn.execute(
            sa.select(users)
            .select_from(users)
            .where(
                (users.c.email == email) & (users.c.domain_name == domain),
            ),
        )
    row = result.first()
    if row is None:
        raise AuthorizationFailed("User credential mismatch.")
    if row.password is None:
        raise AuthorizationFailed("User credential mismatch.")

    try:
        if not _verify_password(password, row.password):
            raise AuthorizationFailed("User credential mismatch.")
    except ValueError as e:
        raise AuthorizationFailed("User credential mismatch.") from e

    row_mapping: sa.RowMapping = row._mapping
    return row_mapping
