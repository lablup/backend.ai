from __future__ import annotations

import enum
import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Self,
    Sequence,
    cast,
    override,
)
from uuid import UUID

import bcrypt
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, relationship, selectinload
from sqlalchemy.types import VARCHAR, TypeDecorator

from ai.backend.common.types import CIStrEnum
from ai.backend.logging import BraceStyleAdapter

from .base import (
    Base,
    EnumValueType,
    IDColumn,
    IPColumn,
    mapper_registry,
)
from .exceptions import ObjectNotFound
from .types import (
    QueryCondition,
    QueryOption,
    QuerySingleCondition,
    load_related_field,
)
from .utils import ExtendedAsyncSAEngine, execute_with_txn_retry

if TYPE_CHECKING:
    from .keypair import KeyPairRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "users",
    "UserRow",
    "UserRole",
    "UserStatus",
    "ACTIVE_USER_STATUSES",
    "INACTIVE_USER_STATUSES",
)


class PasswordColumn(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        return _hash_password(value)


class UserRole(CIStrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


class UserStatus(enum.StrEnum):
    """
    User account status.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"

    @override
    @classmethod
    def _missing_(cls, value: Any) -> Optional[UserStatus]:
        assert isinstance(value, str)
        match value.upper():
            case "ACTIVE":
                return cls.ACTIVE
            case "INACTIVE":
                return cls.INACTIVE
            case "DELETED":
                return cls.DELETED
            case "BEFORE-VERIFICATION" | "BEFORE_VERIFICATION":
                return cls.BEFORE_VERIFICATION
        return None


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


class UserRow(Base):
    __table__ = users
    # from .keypair import KeyPairRow

    sessions = relationship("SessionRow", back_populates="user")
    domain = relationship("DomainRow", back_populates="users")
    groups = relationship("AssocGroupUserRow", back_populates="user")
    resource_policy_row = relationship("UserResourcePolicyRow", back_populates="users")
    keypairs = relationship("KeyPairRow", back_populates="user_row", foreign_keys="KeyPairRow.user")
    kernels = relationship("KernelRow", back_populates="user_row")

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
        condition: QueryCondition,
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
        query_stmt = sa.select(UserRow).where(condition.final_sql_condition)

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
            QueryCondition.single(by_user_uuid(user_uuid)),
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


def by_user_uuid(
    user_uuid: UUID,
) -> QuerySingleCondition:
    return UserRow.uuid == user_uuid


def by_username(
    username: str,
) -> QuerySingleCondition:
    return UserRow.username == username


def by_user_email(
    email: str,
) -> QuerySingleCondition:
    return UserRow.email == email


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt(rounds=12)).decode("utf8")


def _verify_password(guess: str, hashed: str) -> bool:
    return bcrypt.checkpw(guess.encode("utf8"), hashed.encode("utf8"))


def compare_to_hashed_password(raw_password: str, hashed_password: str) -> bool:
    """
    Compare a raw string password value to hased password.
    """
    return _verify_password(raw_password, hashed_password)


async def check_credential(
    db: SAEngine,
    domain: str,
    email: str,
    password: str,
) -> Any:
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
        if _verify_password(password, row["password"]):
            return row
    except ValueError:
        return None
    return None
