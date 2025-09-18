from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Self,
    Sequence,
    cast,
)
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import foreign, joinedload, relationship, selectinload
from sqlalchemy.types import VARCHAR, TypeDecorator

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.model_serving.types import UserData as ModelServingUserData
from ai.backend.manager.data.user.types import UserCreator, UserData, UserRole, UserStatus
from ai.backend.manager.models.hasher.types import HashInfo, PasswordInfo

from .base import (
    Base,
    EnumValueType,
    IDColumn,
    IPColumn,
    mapper_registry,
)
from .exceptions import ObjectNotFound
from .hasher import PasswordHasherFactory
from .types import (
    QueryCondition,
    QueryOption,
    load_related_field,
)
from .utils import ExtendedAsyncSAEngine, execute_with_txn_retry

if TYPE_CHECKING:
    from .keypair import KeyPairRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__: Sequence[str] = (
    "users",
    "UserRow",
    "UserRole",  # For compatibility with existing code
    "UserStatus",  # For compatibility with existing code
    "ACTIVE_USER_STATUSES",
    "INACTIVE_USER_STATUSES",
    "PasswordHashAlgorithm",
    "compare_to_hashed_password",
    "check_credential_with_migration",
    "check_credential",
)


class PasswordColumn(TypeDecorator):
    """Custom column type that prevents direct password assignment.

    Passwords should be set using proper functions that have access to config:
    - Use check_credential() for login with gradual migration
    - Use explicit UPDATE queries with pre-hashed passwords

    This column type is kept for backward compatibility but should not be used
    for setting passwords directly.
    """

    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None

        if not isinstance(value, PasswordInfo):
            raise ValueError("Password must be set using PasswordInfo for hashing.")

        hash_info = value.generate_new_hash()
        return hash_info.to_string()


ACTIVE_USER_STATUSES = (UserStatus.ACTIVE,)

INACTIVE_USER_STATUSES = (
    UserStatus.INACTIVE,
    UserStatus.DELETED,
    UserStatus.BEFORE_VERIFICATION,
)


users = sa.Table(
    "users",
    mapper_registry.metadata,
    IDColumn("uuid"),
    sa.Column("username", sa.String(length=64), unique=True),
    sa.Column("email", sa.String(length=64), index=True, nullable=False, unique=True),
    sa.Column("password", PasswordColumn()),
    sa.Column("need_password_change", sa.Boolean),
    sa.Column(
        "password_changed_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
    ),
    sa.Column("full_name", sa.String(length=64)),
    sa.Column("description", sa.String(length=500)),
    sa.Column("status", EnumValueType(UserStatus), default=UserStatus.ACTIVE, nullable=False),
    sa.Column("status_info", sa.Unicode(), nullable=True, default=sa.null()),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    ),
    #: Field for synchronization with external services.
    sa.Column("integration_id", sa.String(length=512)),
    sa.Column("domain_name", sa.String(length=64), sa.ForeignKey("domains.name"), index=True),
    sa.Column("role", EnumValueType(UserRole), default=UserRole.USER),
    sa.Column("allowed_client_ip", pgsql.ARRAY(IPColumn), nullable=True),
    sa.Column("totp_key", sa.String(length=32)),
    sa.Column("totp_activated", sa.Boolean, server_default=sa.false(), default=False),
    sa.Column("totp_activated_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column(
        "resource_policy",
        sa.String(length=256),
        sa.ForeignKey("user_resource_policies.name"),
        nullable=False,
    ),
    sa.Column(
        "sudo_session_enabled",
        sa.Boolean,
        default=False,
        nullable=False,
    ),
    sa.Column(
        "main_access_key",
        sa.String(length=20),
        sa.ForeignKey("keypairs.access_key", ondelete="SET NULL"),
        nullable=True,  # keypairs.user is non-nullable
    ),
    sa.Column("container_uid", sa.Integer, nullable=True, server_default=sa.null()),
    sa.Column("container_main_gid", sa.Integer, nullable=True, server_default=sa.null()),
    sa.Column("container_gids", sa.ARRAY(sa.Integer), nullable=True, server_default=sa.null()),
)


# Defined for avoiding circular import
def _get_session_row_join_condition():
    from ai.backend.manager.models.session import SessionRow

    return UserRow.uuid == foreign(SessionRow.user_uuid)


def _get_kernel_row_join_condition():
    from ai.backend.manager.models.kernel import KernelRow

    return UserRow.uuid == foreign(KernelRow.user_uuid)


class UserRow(Base):
    __table__ = users
    # from .keypair import KeyPairRow

    sessions = relationship(
        "SessionRow",
        back_populates="user",
        primaryjoin=_get_session_row_join_condition,
        foreign_keys="SessionRow.user_uuid",
    )
    kernels = relationship(
        "KernelRow",
        back_populates="user_row",
        primaryjoin=_get_kernel_row_join_condition,
        foreign_keys="KernelRow.user_uuid",
    )
    domain = relationship("DomainRow", back_populates="users")
    groups = relationship("AssocGroupUserRow", back_populates="user")
    resource_policy_row = relationship("UserResourcePolicyRow", back_populates="users")
    keypairs = relationship("KeyPairRow", back_populates="user_row", foreign_keys="KeyPairRow.user")

    created_endpoints = relationship(
        "EndpointRow",
        back_populates="created_user_row",
        primaryjoin="foreign(EndpointRow.created_user) == UserRow.uuid",
    )
    owned_endpoints = relationship(
        "EndpointRow",
        back_populates="session_owner_row",
        primaryjoin="foreign(EndpointRow.session_owner) == UserRow.uuid",
    )

    main_keypair = relationship("KeyPairRow", foreign_keys=users.c.main_access_key)

    vfolder_rows = relationship(
        "VFolderRow",
        back_populates="user_row",
        primaryjoin="UserRow.uuid == foreign(VFolderRow.user)",
    )

    role_assignments = relationship(
        "UserRoleRow",
        back_populates="user_row",
        primaryjoin="UserRow.uuid == foreign(UserRoleRow.user_id)",
    )

    @classmethod
    def from_creator(cls, creator: UserCreator) -> Self:
        return cls(
            username=creator.username,
            email=creator.email,
            password=creator.password,
            need_password_change=creator.need_password_change
            if creator.need_password_change is not None
            else False,
            full_name=creator.full_name,
            description=creator.description,
            status=creator.status if creator.status is not None else UserStatus.BEFORE_VERIFICATION,
            domain_name=creator.domain_name,
            role=creator.role if creator.role is not None else UserRole.USER,
            resource_policy=creator.resource_policy
            if creator.resource_policy is not None
            else "default",
            allowed_client_ip=creator.allowed_client_ip,
            totp_activated=creator.totp_activated if creator.totp_activated is not None else False,
            sudo_session_enabled=creator.sudo_session_enabled
            if creator.sudo_session_enabled is not None
            else False,
            container_uid=creator.container_uid,
            container_main_gid=creator.container_main_gid,
            container_gids=creator.container_gids,
        )

    @classmethod
    def load_keypairs(cls) -> Callable:
        from .keypair import KeyPairRow

        return selectinload(UserRow.keypairs).options(joinedload(KeyPairRow.resource_policy_row))

    @classmethod
    def load_main_keypair(cls) -> Callable:
        from .keypair import KeyPairRow

        return joinedload(UserRow.main_keypair).options(joinedload(KeyPairRow.resource_policy_row))

    @classmethod
    def load_resource_policy(cls) -> Callable:
        return joinedload(UserRow.resource_policy_row)

    @classmethod
    async def query_user_by_uuid(
        cls,
        user_uuid: UUID,
        db_session: SASession,
    ) -> Optional[Self]:
        user_query = (
            sa.select(UserRow)
            .where(UserRow.uuid == user_uuid)
            .options(
                joinedload(UserRow.main_keypair),
                selectinload(UserRow.keypairs),
            )
        )
        user_row = await db_session.scalar(user_query)
        return user_row

    @classmethod
    async def query_by_condition(
        cls,
        conditions: Sequence[QueryCondition],
        options: Sequence[QueryOption] = tuple(),
        *,
        db: ExtendedAsyncSAEngine,
    ) -> list[Self]:
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

        async def fetch(db_session: SASession) -> list[Self]:
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
    ) -> Self:
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
                load_related_field(cls.load_keypairs),
                load_related_field(cls.load_main_keypair),
                load_related_field(cls.load_resource_policy),
            ],
            db=db,
        )
        if not rows:
            raise ObjectNotFound(f"User with id {user_uuid} not found")
        return rows[0]

    def get_main_keypair_row(self) -> Optional[KeyPairRow]:
        # `cast()` requires import of KeyPairRow
        from .keypair import KeyPairRow

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
            role=self.role.value,
            resource_policy=self.resource_policy,
            allowed_client_ip=self.allowed_client_ip,
            totp_activated=self.totp_activated,
            totp_activated_at=self.totp_activated_at,
            sudo_session_enabled=self.sudo_session_enabled,
            main_access_key=self.main_access_key,
            container_uid=self.container_uid,
            container_main_gid=self.container_main_gid,
            container_gids=self.container_gids,
        )


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
    db: SAEngine,
    domain: str,
    email: str,
    target_password_info: PasswordInfo,
) -> Any:
    """
    Check user credentials and optionally migrate password hash if needed.

    Args:
        db: Database engine
        domain: User's domain
        email: User's email
        target_password_info: Password configuration containing password and target hash settings

    Returns:
        User row if credentials are valid, None otherwise
    """
    async with db.begin_readonly() as conn:
        result = await conn.execute(
            sa.select([users])
            .select_from(users)
            .where(
                (users.c.email == email) & (users.c.domain_name == domain),
            ),
        )
    row = result.first()
    if row is None:
        return None
    if row["password"] is None:
        # user password is not set.
        return None

    try:
        if not _verify_password(target_password_info.password, row["password"]):
            return None
    except ValueError:
        return None

    # Password is valid, check if we need to migrate the hash
    current_hash_info = HashInfo.from_hash_string(row["password"])
    if current_hash_info is None:
        # Shouldn't happen since password was just verified
        return row

    if target_password_info.need_migration(current_hash_info):
        # Re-hash the password with the new algorithm using the provided PasswordInfo
        # Update the user's password hash asynchronously
        async with db.begin() as conn:
            await conn.execute(
                sa.update(users)
                .where((users.c.email == email) & (users.c.domain_name == domain))
                .values(password=target_password_info)
            )

    return row


async def check_credential(
    db: SAEngine,
    domain: str,
    email: str,
    password: str,
) -> Any:
    """
    Check user credentials without migration (for signout, update password, etc.)

    Args:
        db: Database engine
        domain: User's domain
        email: User's email
        password: Plain text password to verify

    Returns:
        User row if credentials are valid, None otherwise
    """
    async with db.begin_readonly() as conn:
        result = await conn.execute(
            sa.select([users])
            .select_from(users)
            .where(
                (users.c.email == email) & (users.c.domain_name == domain),
            ),
        )
    row = result.first()
    if row is None:
        return None
    if row["password"] is None:
        # user password is not set.
        return None

    try:
        if not _verify_password(password, row["password"]):
            return None
    except ValueError:
        return None

    return row
