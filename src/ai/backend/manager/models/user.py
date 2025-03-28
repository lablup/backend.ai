from __future__ import annotations

import enum
import logging
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Optional, Self, Sequence, cast
from uuid import UUID, uuid4

import aiotools
import bcrypt
import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, relationship, selectinload
from sqlalchemy.types import VARCHAR, TypeDecorator

from ai.backend.common import redis_helper
from ai.backend.common.types import RedisConnectionInfo, Sentinel, VFolderID
from ai.backend.logging import BraceStyleAdapter

from ..api.exceptions import VFolderOperationFailed
from .base import (
    Base,
    EnumValueType,
    IDColumn,
    IPColumn,
    Item,
    PaginatedList,
    batch_multiresult,
    batch_result,
    mapper_registry,
)
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser, enum_field_getter
from .utils import ExtendedAsyncSAEngine, execute_with_txn_retry

if TYPE_CHECKING:
    from ai.backend.manager.services.users.actions.create_user import (
        CreateUserAction,
        CreateUserActionResult,
    )
    from ai.backend.manager.services.users.actions.delete_user import (
        DeleteUserAction,
        DeleteUserActionResult,
    )
    from ai.backend.manager.services.users.actions.modify_user import (
        ModifyUserAction,
        ModifyUserActionResult,
    )
    from ai.backend.manager.services.users.type import UserData

    from .gql import GraphQueryContext
    from .keypair import KeyPairRow
    from .storage import StorageSessionManager

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "users",
    "UserRow",
    "User",
    "UserList",
    "UserGroup",
    "UserRole",
    "UserInput",
    "ModifyUserInput",
    "CreateUser",
    "ModifyUser",
    "DeleteUser",
    "UserStatus",
    "ACTIVE_USER_STATUSES",
    "INACTIVE_USER_STATUSES",
)


class PasswordColumn(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        return _hash_password(value)


class UserRole(enum.StrEnum):
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


class UserGroup(graphene.ObjectType):
    id = graphene.UUID()
    name = graphene.String()

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[UserGroup]:
        if row is None:
            return None
        return cls(
            id=row["id"],
            name=row["name"],
        )

    @classmethod
    async def batch_load_by_user_id(cls, ctx: GraphQueryContext, user_ids: Sequence[UUID]):
        async with ctx.db.begin() as conn:
            from .group import association_groups_users as agus
            from .group import groups

            j = agus.join(groups, agus.c.group_id == groups.c.id)
            query = (
                sa.select([agus.c.user_id, groups.c.name, groups.c.id])
                .select_from(j)
                .where(agus.c.user_id.in_(user_ids))
            )
            return await batch_multiresult(
                ctx,
                conn,
                query,
                cls,
                user_ids,
                lambda row: row["user_id"],
            )


class User(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    uuid = graphene.UUID()  # legacy
    username = graphene.String()
    email = graphene.String()
    need_password_change = graphene.Boolean()
    full_name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    status = graphene.String()
    status_info = graphene.String()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    domain_name = graphene.String()
    role = graphene.String()
    resource_policy = graphene.String()
    allowed_client_ip = graphene.List(lambda: graphene.String)
    totp_activated = graphene.Boolean()
    totp_activated_at = GQLDateTime()
    sudo_session_enabled = graphene.Boolean()
    main_access_key = graphene.String(
        description=(
            "Added in 24.03.0. Used as the default authentication credential for password-based"
            " logins and sets the user's total resource usage limit. User's main_access_key cannot"
            " be deleted, and only super-admin can replace main_access_key."
        )
    )
    container_uid = graphene.Int(
        description="Added in 25.2.0. The user ID (UID) assigned to processes running inside the container."
    )
    container_main_gid = graphene.Int(
        description="Added in 25.2.0. The primary group ID (GID) assigned to processes running inside the container."
    )
    container_gids = graphene.List(
        lambda: graphene.Int,
        description="Added in 25.2.0. Supplementary group IDs assigned to processes running inside the container.",
    )

    groups = graphene.List(lambda: UserGroup)

    async def resolve_groups(
        self,
        info: graphene.ResolveInfo,
    ) -> Iterable[UserGroup]:
        ctx: GraphQueryContext = info.context
        manager = ctx.dataloader_manager
        loader = manager.get_loader(ctx, "UserGroup.by_user_id")
        return await loader.load(self.id)

    @classmethod
    def from_dto(cls, dto: UserData) -> Self:
        return cls(
            id=dto.id,
            uuid=dto.uuid,  # legacy
            username=dto.username,
            email=dto.email,
            need_password_change=dto.need_password_change,
            full_name=dto.full_name,
            description=dto.description,
            is_active=dto.is_active,
            status=dto.status,
            status_info=dto.status_info,
            created_at=dto.created_at,
            modified_at=dto.modified_at,
            domain_name=dto.domain_name,
            role=dto.role,
            resource_policy=dto.resource_policy,
            allowed_client_ip=dto.allowed_client_ip,
            totp_activated=dto.totp_activated,
            totp_activated_at=dto.totp_activated_at,
            sudo_session_enabled=dto.sudo_session_enabled,
            main_access_key=dto.main_access_key,
            container_uid=dto.container_uid,
            container_main_gid=dto.container_main_gid,
            container_gids=dto.container_gids,
        )

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row,
    ) -> User:
        return cls(
            id=row["uuid"],
            uuid=row["uuid"],
            username=row["username"],
            email=row["email"],
            need_password_change=row["need_password_change"],
            full_name=row["full_name"],
            description=row["description"],
            is_active=True if row["status"] == UserStatus.ACTIVE else False,  # legacy
            status=row["status"],
            status_info=row["status_info"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            domain_name=row["domain_name"],
            role=row["role"],
            resource_policy=row["resource_policy"],
            allowed_client_ip=row["allowed_client_ip"],
            totp_activated=row["totp_activated"],
            totp_activated_at=row["totp_activated_at"],
            sudo_session_enabled=row["sudo_session_enabled"],
            main_access_key=row["main_access_key"],
            container_uid=row["container_uid"],
            container_main_gid=row["container_main_gid"],
            container_gids=row["container_gids"],
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[User]:
        """
        Load user's information. Group names associated with the user are also returned.
        """
        if group_id is not None:
            from .group import association_groups_users as agus

            j = users.join(agus, agus.c.user_id == users.c.uuid)
            query = sa.select([users]).select_from(j).where(agus.c.group_id == group_id)
        else:
            query = sa.select([users]).select_from(users)
        if ctx.user["role"] != UserRole.SUPERADMIN:
            query = query.where(users.c.domain_name == ctx.user["domain_name"])
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        if limit is not None:
            query = query.limit(limit)
        async with ctx.db.begin_readonly() as conn:
            return [cls.from_row(ctx, row) async for row in (await conn.stream(query))]

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "uuid": ("uuid", None),
        "username": ("username", None),
        "email": ("email", None),
        "need_password_change": ("need_password_change", None),
        "full_name": ("full_name", None),
        "description": ("description", None),
        "is_active": ("is_active", None),
        "status": ("status", enum_field_getter(UserStatus)),
        "status_info": ("status_info", None),
        "created_at": ("created_at", dtparse),
        "modified_at": ("modified_at", dtparse),
        "domain_name": ("domain_name", None),
        "role": ("role", enum_field_getter(UserRole)),
        "resource_policy": ("domain_name", None),
        "allowed_client_ip": ("allowed_client_ip", None),
        "totp_activated": ("totp_activated", None),
        "totp_activated_at": ("totp_activated_at", dtparse),
        "sudo_session_enabled": ("sudo_session_enabled", None),
        "main_access_key": ("main_access_key", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "uuid": ("uuid", None),
        "username": ("username", None),
        "email": ("email", None),
        "need_password_change": ("need_password_change", None),
        "full_name": ("full_name", None),
        "is_active": ("is_active", None),
        "status": ("status", None),
        "status_info": ("status_info", None),
        "created_at": ("created_at", None),
        "modified_at": ("modified_at", None),
        "domain_name": ("domain_name", None),
        "role": ("role", None),
        "resource_policy": ("resource_policy", None),
        "totp_activated": ("totp_activated", None),
        "totp_activated_at": ("totp_activated_at", None),
        "sudo_session_enabled": ("sudo_session_enabled", None),
        "main_access_key": ("main_access_key", None),
    }

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        status: Optional[str] = None,
        filter: Optional[str] = None,
    ) -> int:
        if group_id is not None:
            from .group import association_groups_users as agus

            j = users.join(agus, agus.c.user_id == users.c.uuid)
            query = sa.select([sa.func.count()]).select_from(j).where(agus.c.group_id == group_id)
        else:
            query = sa.select([sa.func.count()]).select_from(users)
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        if filter is not None:
            if group_id is not None:
                qfparser = QueryFilterParser({
                    k: ("users_" + v[0], v[1])
                    for k, v in cls._queryfilter_fieldspec.items()
                    if isinstance(v[0], str)
                })
            else:
                qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
        return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        status: Optional[str] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[User]:
        if group_id is not None:
            from .group import association_groups_users as agus

            j = users.join(agus, agus.c.user_id == users.c.uuid)
            query = (
                sa.select([users])
                .select_from(j)
                .where(agus.c.group_id == group_id)
                .limit(limit)
                .offset(offset)
            )
        else:
            query = sa.select([users]).select_from(users).limit(limit).offset(offset)
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        if filter is not None:
            if group_id is not None:
                qfparser = QueryFilterParser({
                    k: ("users_" + v[0], v[1])
                    for k, v in cls._queryfilter_fieldspec.items()
                    if isinstance(v[0], str)
                })
            else:
                qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            if group_id is not None:
                qoparser = QueryOrderParser({
                    k: ("users_" + v[0], v[1])
                    for k, v in cls._queryorder_colmap.items()
                    if isinstance(v[0], str)
                })
            else:
                qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(
                users.c.created_at.desc(),
            )
        async with ctx.db.begin_readonly() as conn:
            return [cls.from_row(ctx, row) async for row in (await conn.stream(query))]

    @classmethod
    async def batch_load_by_email(
        cls,
        ctx: GraphQueryContext,
        emails: Optional[Sequence[str]] = None,
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> Sequence[Optional[User]]:
        if not emails:
            return []
        query = sa.select([users]).select_from(users).where(users.c.email.in_(emails))
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                emails,
                lambda row: row["email"],
            )

    @classmethod
    async def batch_load_by_uuid(
        cls,
        ctx: GraphQueryContext,
        user_ids: Optional[Sequence[UUID]] = None,
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> Sequence[Optional[User]]:
        if not user_ids:
            return []
        query = sa.select([users]).select_from(users).where(users.c.uuid.in_(user_ids))
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                user_ids,
                lambda row: row["uuid"],
            )


class UserList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(User, required=True)


class UserInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    password = graphene.String(required=True)
    need_password_change = graphene.Boolean(required=True)
    full_name = graphene.String(required=False, default_value="")
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    status = graphene.String(required=False, default_value=UserStatus.ACTIVE)
    domain_name = graphene.String(required=True, default_value="default")
    role = graphene.String(required=False, default_value=UserRole.USER)
    group_ids = graphene.List(lambda: graphene.String, required=False)
    allowed_client_ip = graphene.List(lambda: graphene.String, required=False, default_value=None)
    totp_activated = graphene.Boolean(required=False, default_value=False)
    resource_policy = graphene.String(required=False, default_value="default")
    sudo_session_enabled = graphene.Boolean(required=False, default_value=False)
    container_uid = graphene.Int(
        required=False,
        description="Added in 25.2.0. The user ID (UID) assigned to processes running inside the container.",
    )
    container_main_gid = graphene.Int(
        required=False,
        description="Added in 25.2.0. The primary group ID (GID) assigned to processes running inside the container.",
    )
    container_gids = graphene.List(
        lambda: graphene.Int,
        required=False,
        description="Added in 25.2.0. Supplementary group IDs assigned to processes running inside the container.",
    )
    # When creating, you MUST set all fields.
    # When modifying, set the field to "None" to skip setting the value.

    def to_action(self, email: str) -> CreateUserAction:
        action = CreateUserAction(
            username=self.username,
            password=self.password,
            email=email,
            need_password_change=self.need_password_change,
            domain_name=self.domain_name,
        )

        if hasattr(self, "full_name"):
            action.full_name = self.full_name
        if hasattr(self, "description"):
            action.description = self.description
        if hasattr(self, "is_active"):
            action.is_active = self.is_active
        if hasattr(self, "status"):
            action.status = UserStatus(self.status)
        if hasattr(self, "role"):
            action.role = UserRole(self.role)
        if hasattr(self, "group_ids"):
            action.group_ids = self.group_ids
        if hasattr(self, "group_ids"):
            action.group_ids = self.group_ids
        if hasattr(self, "allowed_client_ip"):
            action.allowed_client_ip = self.allowed_client_ip
        if hasattr(self, "totp_activated"):
            action.totp_activated = self.totp_activated
        if hasattr(self, "resource_policy"):
            action.resource_policy = self.resource_policy
        if hasattr(self, "sudo_session_enabled"):
            action.sudo_session_enabled = self.sudo_session_enabled

        action.container_uid = (
            self.container_uid if hasattr(self, "container_uid") else Sentinel.TOKEN
        )
        action.container_main_gid = (
            self.container_main_gid if hasattr(self, "container_main_gid") else Sentinel.TOKEN
        )
        action.container_gids = (
            self.container_gids if hasattr(self, "container_gids") else Sentinel.TOKEN
        )

        return action


class ModifyUserInput(graphene.InputObjectType):
    username = graphene.String(required=False)
    password = graphene.String(required=False)
    need_password_change = graphene.Boolean(required=False)
    full_name = graphene.String(required=False)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    status = graphene.String(required=False)
    domain_name = graphene.String(required=False)
    role = graphene.String(required=False)
    group_ids = graphene.List(lambda: graphene.String, required=False)
    allowed_client_ip = graphene.List(lambda: graphene.String, required=False)
    totp_activated = graphene.Boolean(required=False, default=False)
    resource_policy = graphene.String(required=False)
    sudo_session_enabled = graphene.Boolean(required=False, default=False)
    main_access_key = graphene.String(required=False)
    container_uid = graphene.Int(
        required=False,
        description="Added in 25.2.0. The user ID (UID) assigned to processes running inside the container.",
    )
    container_main_gid = graphene.Int(
        required=False,
        description="Added in 25.2.0. The primary group ID (GID) assigned to processes running inside the container.",
    )
    container_gids = graphene.List(
        lambda: graphene.Int,
        required=False,
        description="Added in 25.2.0. Supplementary group IDs assigned to processes running inside the container.",
    )

    def to_action(self, email) -> ModifyUserAction:
        fields = {}

        for field in [
            "username",
            "password",
            "need_password_change",
            "full_name",
            "description",
            "is_active",
            "status",
            "domain_name",
            "role",
            "group_ids",
            "allowed_client_ip",
            "totp_activated",
            "resource_policy",
            "sudo_session_enabled",
            "main_access_key",
            "container_uid",
            "container_main_gid",
            "container_gids",
        ]:
            if hasattr(self, field):
                value = getattr(self, field)
                if field == "status":
                    value = UserStatus(value)
                elif field == "role":
                    value = UserRole(value)
                fields[field] = value
            else:
                fields[field] = Sentinel.TOKEN

        return ModifyUserAction(email=email, **fields)


class PurgeUserInput(graphene.InputObjectType):
    purge_shared_vfolders = graphene.Boolean(required=False, default=False)
    delegate_endpoint_ownership = graphene.Boolean(
        required=False,
        default=False,
        description=(
            "Added in 25.4.0. The default value is `false`. "
            "Indicates whether the user's existing endpoints are delegated to the requester."
        ),
    )


class CreateUser(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        email = graphene.String(required=True)
        props = UserInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    user = graphene.Field(lambda: User, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        email: str,
        props: UserInput,
    ) -> CreateUser:
        graph_ctx: GraphQueryContext = info.context
        action: CreateUserAction = props.to_action(email)

        res: CreateUserActionResult = await graph_ctx.processors.user.create_user.wait_for_complete(
            action
        )

        return cls(
            ok=res.success,
            msg="success" if res.success else "failed",
            user=User.from_dto(res.data) if res.data else None,
        )


class ModifyUser(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        email = graphene.String(required=True)
        props = ModifyUserInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    user = graphene.Field(lambda: User)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        email: str,
        props: ModifyUserInput,
    ) -> ModifyUser:
        graph_ctx: GraphQueryContext = info.context

        action: ModifyUserAction = props.to_action(email)
        res: ModifyUserActionResult = await graph_ctx.processors.user.modify_user.wait_for_complete(
            action
        )

        return cls(
            ok=res.success,
            msg="success" if res.success else "failed",
            user=User.from_dto(res.data) if res.data else None,
        )


class DeleteUser(graphene.Mutation):
    """
    Instead of really deleting user, just mark the account as deleted status.

    All related keypairs will also be inactivated.
    """

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        email = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        email: str,
    ) -> DeleteUser:
        graph_ctx: GraphQueryContext = info.context

        action = DeleteUserAction(email)
        res: DeleteUserActionResult = await graph_ctx.processors.user.delete_user.wait_for_complete(
            action
        )

        return cls(
            ok=res.success,
            msg="success" if res.success else "failed",
        )


class PurgeUser(graphene.Mutation):
    """
    Delete user as well as all user-related DB informations such as keypairs, kernels, etc.

    If target user has virtual folders, they can be purged together or migrated to the superadmin.

    vFolder treatment policy:
      User-type:
      - vfolder is not shared: delete
      - vfolder is shared:
        + if purge_shared_vfolder is True: delete
        + else: change vfolder's owner to requested admin

    This action cannot be undone.
    """

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        email = graphene.String(required=True)
        props = PurgeUserInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        email: str,
        props: PurgeUserInput,
    ) -> PurgeUser:
        from .endpoint import EndpointRow

        graph_ctx: GraphQueryContext = info.context

        async def _delete(db_session: SASession) -> None:
            conn = await db_session.connection()
            user_uuid = await db_session.scalar(
                sa.select(UserRow.uuid).where(UserRow.email == email),
            )
            user_uuid = cast(Optional[UUID], user_uuid)
            log.info("Purging all records of the user {0}...", email)
            if user_uuid is None:
                raise RuntimeError(f"User not found (email: {email})")

            if await cls.user_vfolder_mounted_to_active_kernels(conn, user_uuid):
                raise RuntimeError(
                    "Some of user's virtual folders are mounted to active kernels. "
                    "Terminate those kernels first.",
                )

            if not props.purge_shared_vfolders:
                await cls.migrate_shared_vfolders(
                    conn,
                    deleted_user_uuid=user_uuid,
                    target_user_uuid=graph_ctx.user["uuid"],
                    target_user_email=graph_ctx.user["email"],
                )
            if props.delegate_endpoint_ownership:
                await EndpointRow.delegate_endpoint_ownership(
                    db_session, user_uuid, graph_ctx.user["uuid"], graph_ctx.user["main_access_key"]
                )
                await cls._delete_endpoint(db_session, user_uuid, delete_destroyed_only=True)
            else:
                await cls._delete_endpoint(db_session, user_uuid, delete_destroyed_only=False)
            if await cls._user_has_active_sessions(db_session, user_uuid):
                raise RuntimeError("User has some active sessions. Terminate them first.")
            await cls._delete_sessions(db_session, user_uuid)
            await cls._delete_vfolders(graph_ctx.db, user_uuid, graph_ctx.storage_manager)
            await cls.delete_error_logs(conn, user_uuid)
            await cls.delete_keypairs(conn, graph_ctx.redis_stat, user_uuid)

            await db_session.execute(sa.delete(users).where(users.c.email == email))

        async with graph_ctx.db.connect() as db_conn:
            await execute_with_txn_retry(_delete, graph_ctx.db.begin_session, db_conn)
        return PurgeUser(True, "success")

    @classmethod
    async def migrate_shared_vfolders(
        cls,
        conn: SAConnection,
        deleted_user_uuid: UUID,
        target_user_uuid: UUID,
        target_user_email: str,
    ) -> int:
        """
        Migrate shared virtual folders' ownership to a target user.

        If migrating virtual folder's name collides with target user's already
        existing folder, append random string to the migrating one.

        :param conn: DB connection
        :param deleted_user_uuid: user's UUID who will be deleted
        :param target_user_uuid: user's UUID who will get the ownership of virtual folders

        :return: number of deleted rows
        """
        from . import vfolder_invitations, vfolder_permissions, vfolders

        # Gather target user's virtual folders' names.
        query = (
            sa.select([vfolders.c.name])
            .select_from(vfolders)
            .where(vfolders.c.user == target_user_uuid)
        )
        existing_vfolder_names = [row.name async for row in (await conn.stream(query))]

        # Migrate shared virtual folders.
        # If virtual folder's name collides with target user's folder,
        # append random string to the name of the migrating folder.
        j = vfolder_permissions.join(
            vfolders,
            vfolder_permissions.c.vfolder == vfolders.c.id,
        )
        query = (
            sa.select([vfolders.c.id, vfolders.c.name])
            .select_from(j)
            .where(vfolders.c.user == deleted_user_uuid)
        )
        migrate_updates = []
        async for row in await conn.stream(query):
            name = row.name
            if name in existing_vfolder_names:
                name += f"-{uuid4().hex[:10]}"
            migrate_updates.append({"vid": row.id, "vname": name})
        if migrate_updates:
            # Remove invitations and vfolder_permissions from target user.
            # Target user will be the new owner, and it does not make sense to have
            # invitation and shared permission for its own folder.
            migrate_vfolder_ids = [item["vid"] for item in migrate_updates]
            delete_query = sa.delete(vfolder_invitations).where(
                (vfolder_invitations.c.invitee == target_user_email)
                & (vfolder_invitations.c.vfolder.in_(migrate_vfolder_ids))
            )
            await conn.execute(delete_query)
            delete_query = sa.delete(vfolder_permissions).where(
                (vfolder_permissions.c.user == target_user_uuid)
                & (vfolder_permissions.c.vfolder.in_(migrate_vfolder_ids))
            )
            await conn.execute(delete_query)

            rowcount = 0
            for item in migrate_updates:
                update_query = (
                    sa.update(vfolders)
                    .values(
                        user=target_user_uuid,
                        name=item["vname"],
                    )
                    .where(vfolders.c.id == item["vid"])
                )
                result = await conn.execute(update_query)
                rowcount += result.rowcount
            if rowcount > 0:
                log.info(
                    "{0} shared folders are detected and migrated to user {1}",
                    rowcount,
                    target_user_uuid,
                )
            return rowcount
        else:
            return 0

    @classmethod
    async def _delete_vfolders(
        cls,
        engine: ExtendedAsyncSAEngine,
        user_uuid: UUID,
        storage_manager: StorageSessionManager,
        *,
        delete_service: bool = False,
    ) -> int:
        """
        Delete user's all virtual folders as well as their physical data.

        :param conn: DB connection
        :param user_uuid: user's UUID to delete virtual folders

        :return: number of deleted rows
        """
        from . import (
            VFolderDeletionInfo,
            VFolderRow,
            VFolderStatusSet,
            initiate_vfolder_deletion,
            vfolder_permissions,
            vfolder_status_map,
        )

        target_vfs: list[VFolderDeletionInfo] = []
        async with engine.begin_session() as db_session:
            await db_session.execute(
                vfolder_permissions.delete().where(vfolder_permissions.c.user == user_uuid),
            )
            result = await db_session.scalars(
                sa.select(VFolderRow).where(
                    sa.and_(
                        VFolderRow.user == user_uuid,
                        VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.DELETABLE]),
                    )
                ),
            )
            rows = cast(list[VFolderRow], result.fetchall())
            for vf in rows:
                target_vfs.append(
                    VFolderDeletionInfo(VFolderID.from_row(vf), vf.host, vf.unmanaged_path)
                )

        storage_ptask_group = aiotools.PersistentTaskGroup()
        try:
            await initiate_vfolder_deletion(
                engine,
                target_vfs,
                storage_manager,
                storage_ptask_group,
            )
        except VFolderOperationFailed as e:
            log.error("error on deleting vfolder filesystem directory: {0}", e.extra_msg)
            raise
        deleted_count = len(target_vfs)
        if deleted_count > 0:
            log.info("deleted {0} user's virtual folders ({1})", deleted_count, user_uuid)
        return deleted_count

    @classmethod
    async def user_vfolder_mounted_to_active_kernels(
        cls,
        conn: SAConnection,
        user_uuid: UUID,
    ) -> bool:
        """
        Check if no active kernel is using the user's virtual folders.

        :param conn: DB connection
        :param user_uuid: user's UUID

        :return: True if a virtual folder is mounted to active kernels.
        """
        from . import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels, vfolders

        result = await conn.execute(
            sa.select([vfolders.c.id]).select_from(vfolders).where(vfolders.c.user == user_uuid),
        )
        rows = result.fetchall()
        user_vfolder_ids = [row.id for row in rows]
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        async for row in await conn.stream(query):
            for _mount in row["mounts"]:
                try:
                    vfolder_id = UUID(_mount[2])
                    if vfolder_id in user_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    @classmethod
    async def _user_has_active_sessions(
        cls,
        db_session: SASession,
        user_uuid: UUID,
    ) -> bool:
        """
        Check if the user does not have active sessions.
        """
        from .session import AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES, SessionRow

        active_session_count = await db_session.scalar(
            sa.select(sa.func.count())
            .select_from(SessionRow)
            .where(
                sa.and_(
                    SessionRow.user_uuid == user_uuid,
                    SessionRow.status.in_(AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES),
                )
            ),
        )
        return active_session_count > 0

    @classmethod
    async def _delete_endpoint(
        cls,
        db_session: SASession,
        user_uuid: UUID,
        *,
        delete_destroyed_only: bool = False,
    ) -> None:
        """
        Delete user's all endpoint.
        """
        from .endpoint import EndpointLifecycle, EndpointRow, EndpointTokenRow

        if delete_destroyed_only:
            status_filter = {EndpointLifecycle.DESTROYED}
        else:
            status_filter = {status for status in EndpointLifecycle}
        endpoint_rows = await EndpointRow.list(
            db_session, user_uuid=user_uuid, load_tokens=True, status_filter=status_filter
        )
        token_ids_to_delete = []
        endpoint_ids_to_delete = []
        for row in endpoint_rows:
            token_ids_to_delete.extend([token.id for token in row.tokens])
            endpoint_ids_to_delete.append(row.id)
        await db_session.execute(
            sa.delete(EndpointTokenRow).where(EndpointTokenRow.id.in_(token_ids_to_delete))
        )
        await db_session.execute(
            sa.delete(EndpointRow).where(EndpointRow.id.in_(endpoint_ids_to_delete))
        )

    @classmethod
    async def delete_error_logs(
        cls,
        conn: SAConnection,
        user_uuid: UUID,
    ) -> int:
        """
        Delete user's all error logs.

        :param conn: DB connection
        :param user_uuid: user's UUID to delete error logs
        :return: number of deleted rows
        """
        from .error_logs import error_logs

        result = await conn.execute(sa.delete(error_logs).where(error_logs.c.user == user_uuid))
        if result.rowcount > 0:
            log.info("deleted {0} user's error logs ({1})", result.rowcount, user_uuid)
        return result.rowcount

    @classmethod
    async def _delete_sessions(
        cls,
        db_session: SASession,
        user_uuid: UUID,
    ) -> None:
        """
        Delete user's sessions.
        """
        from .session import SessionRow

        await SessionRow.delete_by_user_id(user_uuid, db_session=db_session)

    @classmethod
    async def delete_keypairs(
        cls,
        conn: SAConnection,
        redis_conn: RedisConnectionInfo,
        user_uuid: UUID,
    ) -> int:
        """
        Delete user's all keypairs.

        :param conn: DB connection
        :param redis_conn: redis connection info
        :param user_uuid: user's UUID to delete keypairs
        :return: number of deleted rows
        """
        from . import keypairs

        ak_rows = await conn.execute(
            sa.select([keypairs.c.access_key]).where(keypairs.c.user == user_uuid),
        )
        if (row := ak_rows.first()) and (access_key := row.access_key):
            # Log concurrency used only when there is at least one keypair.
            await redis_helper.execute(
                redis_conn,
                lambda r: r.delete(f"keypair.concurrency_used.{access_key}"),
            )
            await redis_helper.execute(
                redis_conn,
                lambda r: r.delete(f"keypair.sftp_concurrency_used.{access_key}"),
            )
        result = await conn.execute(
            sa.delete(keypairs).where(keypairs.c.user == user_uuid),
        )
        if result.rowcount > 0:
            log.info("deleted {0} user's keypairs ({1})", result.rowcount, user_uuid)
        return result.rowcount


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
