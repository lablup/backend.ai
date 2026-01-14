from __future__ import annotations

import logging
import uuid as uuid_mod
from collections.abc import Sequence
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Optional,
    cast,
)
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import Mapped, foreign, joinedload, mapped_column, relationship, selectinload
from sqlalchemy.orm.strategy_options import _AbstractLoad

from ai.backend.common.types import ReadableCIDR
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.auth.types import UserCredential
from ai.backend.manager.data.model_serving.types import UserData as ModelServingUserData
from ai.backend.manager.data.user.types import UserData, UserRole, UserStatus
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.base import (
    GUID,
    Base,
    EnumValueType,
    IPColumn,
)
from ai.backend.manager.models.hasher import PasswordHasherFactory
from ai.backend.manager.models.hasher.types import HashInfo, PasswordColumn, PasswordInfo
from ai.backend.manager.models.types import (
    QueryCondition,
    QueryOption,
    load_related_field,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry

if TYPE_CHECKING:
    from ai.backend.manager.models.domain import DomainRow
    from ai.backend.manager.models.endpoint import EndpointRow
    from ai.backend.manager.models.group import AssocGroupUserRow
    from ai.backend.manager.models.kernel import KernelRow
    from ai.backend.manager.models.keypair import KeyPairRow
    from ai.backend.manager.models.rbac_models import UserRoleRow
    from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
    from ai.backend.manager.models.session import SessionRow
    from ai.backend.manager.models.vfolder import VFolderRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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
def _get_session_row_join_condition():
    from ai.backend.manager.models.session import SessionRow

    return UserRow.uuid == foreign(SessionRow.user_uuid)


def _get_kernel_row_join_condition():
    from ai.backend.manager.models.kernel import KernelRow

    return UserRow.uuid == foreign(KernelRow.user_uuid)


def _get_created_endpoints_join_condition():
    from ai.backend.manager.models.endpoint import EndpointRow

    return foreign(EndpointRow.created_user) == UserRow.uuid


def _get_owned_endpoints_join_condition():
    from ai.backend.manager.models.endpoint import EndpointRow

    return foreign(EndpointRow.session_owner) == UserRow.uuid


def _get_vfolder_rows_join_condition():
    from ai.backend.manager.models.vfolder import VFolderRow

    return UserRow.uuid == foreign(VFolderRow.user)


def _get_role_assignments_join_condition():
    from ai.backend.manager.models.rbac_models import UserRoleRow

    return UserRow.uuid == foreign(UserRoleRow.user_id)


def _get_domain_join_condition():
    from ai.backend.manager.models.domain import DomainRow

    return DomainRow.name == foreign(UserRow.domain_name)


def _get_groups_join_condition():
    from ai.backend.manager.models.group import AssocGroupUserRow

    return foreign(AssocGroupUserRow.user_id) == UserRow.uuid


def _get_resource_policy_join_condition():
    from ai.backend.manager.models.resource_policy import UserResourcePolicyRow

    return UserResourcePolicyRow.name == foreign(UserRow.resource_policy)


def _get_keypairs_join_condition():
    from ai.backend.manager.models.keypair import KeyPairRow

    return foreign(KeyPairRow.user) == UserRow.uuid


def _get_main_keypair_join_condition():
    from ai.backend.manager.models.keypair import KeyPairRow

    return KeyPairRow.access_key == foreign(UserRow.main_access_key)


class UserRow(Base):
    __tablename__ = "users"

    uuid: Mapped[uuid_mod.UUID] = mapped_column(
        "uuid", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    username: Mapped[str | None] = mapped_column(
        "username", sa.String(length=64), unique=True, nullable=True
    )
    email: Mapped[str] = mapped_column(
        "email", sa.String(length=64), index=True, nullable=False, unique=True
    )
    password: Mapped[str | None] = mapped_column("password", PasswordColumn(), nullable=True)
    need_password_change: Mapped[bool | None] = mapped_column(
        "need_password_change", sa.Boolean, nullable=True
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        "password_changed_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=True,
    )
    full_name: Mapped[str | None] = mapped_column("full_name", sa.String(length=64), nullable=True)
    description: Mapped[str | None] = mapped_column(
        "description", sa.String(length=500), nullable=True
    )
    status: Mapped[UserStatus] = mapped_column(
        "status", EnumValueType(UserStatus), default=UserStatus.ACTIVE, nullable=False
    )
    status_info: Mapped[str | None] = mapped_column(
        "status_info", sa.Unicode(), nullable=True, default=sa.null()
    )
    created_at: Mapped[datetime | None] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
    )
    modified_at: Mapped[datetime | None] = mapped_column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
        nullable=True,
    )
    #: Field for synchronization with external services.
    integration_id: Mapped[str | None] = mapped_column(
        "integration_id", sa.String(length=512), nullable=True
    )
    domain_name: Mapped[str | None] = mapped_column(
        "domain_name",
        sa.String(length=64),
        sa.ForeignKey("domains.name"),
        index=True,
        nullable=True,
    )
    role: Mapped[UserRole | None] = mapped_column(
        "role", EnumValueType(UserRole), default=UserRole.USER, nullable=True
    )
    allowed_client_ip: Mapped[list[ReadableCIDR] | None] = mapped_column(
        "allowed_client_ip", pgsql.ARRAY(IPColumn), nullable=True
    )
    totp_key: Mapped[str | None] = mapped_column("totp_key", sa.String(length=32), nullable=True)
    totp_activated: Mapped[bool | None] = mapped_column(
        "totp_activated", sa.Boolean, server_default=sa.false(), default=False, nullable=True
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
    main_access_key: Mapped[str | None] = mapped_column(
        "main_access_key",
        sa.String(length=20),
        sa.ForeignKey("keypairs.access_key", ondelete="SET NULL"),
        nullable=True,  # keypairs.user is non-nullable
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
    sessions: Mapped[list[SessionRow]] = relationship(
        "SessionRow",
        back_populates="user",
        primaryjoin=_get_session_row_join_condition,
        foreign_keys="SessionRow.user_uuid",
    )
    kernels: Mapped[list[KernelRow]] = relationship(
        "KernelRow",
        back_populates="user_row",
        primaryjoin=_get_kernel_row_join_condition,
        foreign_keys="KernelRow.user_uuid",
    )
    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow", back_populates="users", primaryjoin=_get_domain_join_condition
    )
    groups: Mapped[list[AssocGroupUserRow]] = relationship(
        "AssocGroupUserRow", back_populates="user", primaryjoin=_get_groups_join_condition
    )
    resource_policy_row: Mapped[UserResourcePolicyRow] = relationship(
        "UserResourcePolicyRow",
        back_populates="users",
        primaryjoin=_get_resource_policy_join_condition,
    )
    keypairs: Mapped[list[KeyPairRow]] = relationship(
        "KeyPairRow",
        back_populates="user_row",
        primaryjoin=_get_keypairs_join_condition,
        foreign_keys="KeyPairRow.user",
    )

    created_endpoints: Mapped[list[EndpointRow]] = relationship(
        "EndpointRow",
        back_populates="created_user_row",
        primaryjoin=_get_created_endpoints_join_condition,
    )
    owned_endpoints: Mapped[list[EndpointRow]] = relationship(
        "EndpointRow",
        back_populates="session_owner_row",
        primaryjoin=_get_owned_endpoints_join_condition,
    )

    main_keypair: Mapped[KeyPairRow | None] = relationship(
        "KeyPairRow",
        primaryjoin=_get_main_keypair_join_condition,
        foreign_keys="UserRow.main_access_key",
    )

    vfolder_rows: Mapped[list[VFolderRow]] = relationship(
        "VFolderRow",
        back_populates="user_row",
        primaryjoin=_get_vfolder_rows_join_condition,
    )

    role_assignments: Mapped[list[UserRoleRow]] = relationship(
        "UserRoleRow",
        back_populates="user_row",
        primaryjoin=_get_role_assignments_join_condition,
    )

    @classmethod
    def load_keypairs(cls) -> _AbstractLoad:
        from ai.backend.manager.models.keypair import KeyPairRow

        return selectinload(UserRow.keypairs).options(joinedload(KeyPairRow.resource_policy_row))

    @classmethod
    def load_main_keypair(cls) -> _AbstractLoad:
        from ai.backend.manager.models.keypair import KeyPairRow

        return joinedload(UserRow.main_keypair).options(joinedload(KeyPairRow.resource_policy_row))

    @classmethod
    def load_resource_policy(cls) -> _AbstractLoad:
        return joinedload(UserRow.resource_policy_row)

    @classmethod
    async def query_by_condition(
        cls,
        conditions: Sequence[QueryCondition],
        options: Sequence[QueryOption] = tuple(),
        *,
        db: ExtendedAsyncSAEngine,
    ) -> Sequence[UserRow]:
        """
        Query user rows by condition.
        Args:
            condition: QueryCondition.
            options: A sequence of query options.
            db: Database engine.
        Returns:
            A list of UserRow instances that match the condition.
        Raises:
            EmptySQLCondition: If condition is empty.
        """
        query_stmt = sa.select(UserRow)
        for cond in conditions:
            query_stmt = cond(query_stmt)

        for option in options:
            query_stmt = option(query_stmt)

        async def fetch(db_session: SASession) -> Sequence[UserRow]:
            return (await db_session.scalars(query_stmt)).all()

        async with db.connect() as db_conn:
            return await execute_with_txn_retry(
                fetch,
                db.begin_readonly_session,
                db_conn,
            )

    @classmethod
    async def get_by_id_with_policies(
        cls,
        user_uuid: UUID,
        *,
        db: ExtendedAsyncSAEngine,
    ) -> UserRow:
        """
        Query user row by UUID with related policies.
        Args:
            user_uuid: User UUID.
            db: Database engine.
        Returns:
            The UserRow instance that matches the UUID.
        Raises:
            ObjectNotFound: If user not found.
        """
        rows = await cls.query_by_condition(
            [by_user_uuid(user_uuid)],
            [
                load_related_field(cls.load_keypairs()),
                load_related_field(cls.load_main_keypair()),
                load_related_field(cls.load_resource_policy()),
            ],
            db=db,
        )
        if not rows:
            raise ObjectNotFound(f"User with id {user_uuid} not found")
        return rows[0]

    def get_main_keypair_row(self) -> Optional[KeyPairRow]:
        # `cast()` requires import of KeyPairRow
        from ai.backend.manager.models.keypair import KeyPairRow

        keypair_candidate: Optional[KeyPairRow] = None
        main_keypair_row = cast(Optional[KeyPairRow], self.main_keypair)
        if main_keypair_row is None:
            keypair_rows = cast(list[KeyPairRow], self.keypairs)
            active_keypairs = [row for row in keypair_rows if row.is_active]
            for row in active_keypairs:
                if keypair_candidate is None or not keypair_candidate.is_admin:
                    keypair_candidate = row
                    break
            if keypair_candidate is not None:
                self.main_keypair = keypair_candidate
        else:
            keypair_candidate = main_keypair_row
        return keypair_candidate

    def to_model_serving_user_data(self) -> ModelServingUserData:
        return ModelServingUserData(
            uuid=self.uuid,
            email=self.email,
        )

    def to_data(self) -> UserData:
        return UserData(
            id=self.uuid,
            uuid=self.uuid,
            username=self.username,
            email=self.email,
            need_password_change=self.need_password_change,
            full_name=self.full_name,
            description=self.description,
            is_active=self.status == UserStatus.ACTIVE,
            status=self.status.value,
            status_info=self.status_info,
            created_at=self.created_at,
            modified_at=self.modified_at,
            domain_name=self.domain_name,
            role=self.role,
            resource_policy=self.resource_policy,
            allowed_client_ip=[str(ip) for ip in self.allowed_client_ip]
            if self.allowed_client_ip
            else None,
            totp_activated=self.totp_activated,
            totp_activated_at=self.totp_activated_at,
            sudo_session_enabled=self.sudo_session_enabled,
            main_access_key=self.main_access_key,
            container_uid=self.container_uid,
            container_main_gid=self.container_main_gid,
            container_gids=self.container_gids,
        )

    def to_credential(self) -> UserCredential:
        """Convert UserRow to UserCredential for authentication."""
        return UserCredential(
            uuid=self.uuid,
            username=self.username,
            email=self.email,
            need_password_change=self.need_password_change,
            password_changed_at=self.password_changed_at,
            full_name=self.full_name,
            status=self.status,
            status_info=self.status_info,
            modified_at=self.modified_at,
            integration_id=self.integration_id,
            domain_name=self.domain_name,
            role=self.role,
            allowed_client_ip=self.allowed_client_ip,
            totp_key=self.totp_key,
            totp_activated=self.totp_activated,
            resource_policy=self.resource_policy,
            sudo_session_enabled=self.sudo_session_enabled,
            main_access_key=self.main_access_key,
        )


# For compatibility
users = UserRow.__table__


def by_user_uuid(
    user_uuid: UUID,
) -> QueryCondition:
    def _by_user_uuid(
        query_stmt: sa.sql.Select,
    ) -> sa.sql.Select:
        return query_stmt.where(UserRow.uuid == user_uuid)

    return _by_user_uuid


def by_username(
    username: str,
) -> QueryCondition:
    def _by_username(
        query_stmt: sa.sql.Select,
    ) -> sa.sql.Select:
        return query_stmt.where(UserRow.username == username)

    return _by_username


def by_user_email(
    email: str,
) -> QueryCondition:
    def _by_email(
        query_stmt: sa.sql.Select,
    ) -> sa.sql.Select:
        return query_stmt.where(UserRow.email == email)

    return _by_email


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
    except ValueError:
        raise AuthorizationFailed("User credential mismatch.")

    # Password is valid, check if we need to migrate the hash
    current_hash_info = HashInfo.from_hash_string(row.password)
    if current_hash_info is None:
        # Shouldn't happen since password was just verified
        return row._mapping

    if target_password_info.need_migration(current_hash_info):
        # Re-hash the password with the new algorithm using the provided PasswordInfo
        # Update the user's password hash asynchronously
        async with db.begin() as conn:
            await conn.execute(
                sa.update(users)
                .where((users.c.email == email) & (users.c.domain_name == domain))
                .values(password=target_password_info)
            )

    return row._mapping


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
    except ValueError:
        raise AuthorizationFailed("User credential mismatch.")

    return row._mapping
