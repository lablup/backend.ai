from __future__ import annotations

import enum
import logging
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Optional, Self, Sequence, cast
from uuid import UUID

import bcrypt
import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, relationship, selectinload
from sqlalchemy.types import VARCHAR, TypeDecorator

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.types import OptionalState

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
from .utils import define_state

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
        UserModifiableFields,
    )
    from ai.backend.manager.services.users.actions.purge_user import (
        PurgeUserAction,
        PurgeUserActionResult,
    )
    from ai.backend.manager.services.users.type import UserData, UserInfoContext

    from .gql import GraphQueryContext
    from .keypair import KeyPairRow

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
        def value_or_none(value: Any) -> Optional[Any]:
            return value if value is not Undefined else None

        return CreateUserAction(
            username=self.username,
            password=self.password,
            email=email,
            need_password_change=self.need_password_change,
            domain_name=self.domain_name,
            full_name=value_or_none(self.full_name),
            description=value_or_none(self.description),
            is_active=value_or_none(self.is_active),
            status=UserStatus(self.status) if self.status is not Undefined else None,
            role=UserRole(self.role) if self.role is not Undefined else None,
            allowed_client_ip=value_or_none(self.allowed_client_ip),
            totp_activated=value_or_none(self.totp_activated),
            resource_policy=value_or_none(self.resource_policy),
            sudo_session_enabled=value_or_none(self.sudo_session_enabled),
            group_ids=value_or_none(self.group_ids),
            container_uid=value_or_none(self.container_uid),
            container_main_gid=value_or_none(self.container_main_gid),
            container_gids=value_or_none(self.container_gids),
        )


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

    def to_action(self, email: str) -> ModifyUserAction:
        def value_or_none(value: Any) -> Optional[Any]:
            return value if value is not Undefined else None

        modfifialble_fields = UserModifiableFields(
            username=OptionalState(
                "username",
                define_state(self.username),
                value_or_none(self.username),
            ),
            password=OptionalState(
                "password",
                define_state(self.password),
                value_or_none(self.password),
            ),
            need_password_change=OptionalState(
                "need_password_change",
                define_state(self.need_password_change),
                value_or_none(self.need_password_change),
            ),
            full_name=OptionalState(
                "full_name",
                define_state(self.full_name),
                value_or_none(self.full_name),
            ),
            description=OptionalState(
                "description",
                define_state(self.description),
                value_or_none(self.description),
            ),
            is_active=OptionalState(
                "is_active",
                define_state(self.is_active),
                value_or_none(self.is_active),
            ),
            status=OptionalState(
                "status",
                define_state(self.status),
                UserStatus(self.status) if self.status is not Undefined else None,
            ),
            domain_name=OptionalState(
                "domain_name",
                define_state(self.domain_name),
                value_or_none(self.domain_name),
            ),
            role=OptionalState(
                "role",
                define_state(self.role),
                UserRole(self.role) if self.role is not Undefined else None,
            ),
            group_ids=OptionalState(
                "group_ids",
                define_state(self.group_ids),
                value_or_none(self.group_ids),
            ),
            allowed_client_ip=OptionalState(
                "allowed_client_ip",
                define_state(self.allowed_client_ip),
                value_or_none(self.allowed_client_ip),
            ),
            totp_activated=OptionalState(
                "totp_activated",
                define_state(self.totp_activated),
                value_or_none(self.totp_activated),
            ),
            resource_policy=OptionalState(
                "resource_policy",
                define_state(self.resource_policy),
                value_or_none(self.resource_policy),
            ),
            sudo_session_enabled=OptionalState(
                "sudo_session_enabled",
                define_state(self.sudo_session_enabled),
                value_or_none(self.sudo_session_enabled),
            ),
            main_access_key=OptionalState(
                "main_access_key",
                define_state(self.main_access_key),
                value_or_none(self.main_access_key),
            ),
            container_uid=OptionalState(
                "container_uid",
                define_state(self.container_uid),
                value_or_none(self.container_uid),
            ),
            container_main_gid=OptionalState(
                "container_main_gid",
                define_state(self.container_main_gid),
                value_or_none(self.container_main_gid),
            ),
            container_gids=OptionalState(
                "container_gids",
                define_state(self.container_gids),
                value_or_none(self.container_gids),
            ),
        )

        return ModifyUserAction(
            email=email,
            modifiable_fields=modfifialble_fields,
        )


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

    def to_action(self, email: str, user_info_ctx: UserInfoContext) -> PurgeUserAction:
        return PurgeUserAction(
            user_info_ctx=user_info_ctx,
            email=email,
            purge_shared_vfolders=OptionalState(
                "purge_shared_vfolders",
                define_state(self.purge_shared_vfolders),
                self.purge_shared_vfolders if self.purge_shared_vfolders is not Undefined else None,
            ),
            delegate_endpoint_ownership=OptionalState(
                "delegate_endpoint_ownership",
                define_state(self.delegate_endpoint_ownership),
                self.delegate_endpoint_ownership
                if self.delegate_endpoint_ownership is not Undefined
                else None,
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
        graph_ctx: GraphQueryContext = info.context
        user_info_ctx = UserInfoContext(
            uuid=graph_ctx.user["uuid"],
            email=graph_ctx.user["email"],
            main_access_key=graph_ctx.user["main_access_key"],
        )
        action = props.to_action(email, user_info_ctx)

        res: PurgeUserActionResult = await graph_ctx.processors.user.purge_user.wait_for_complete(
            action
        )

        return cls(
            ok=res.success,
            msg="success" if res.success else "failed",
        )


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
