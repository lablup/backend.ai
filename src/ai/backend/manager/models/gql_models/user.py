from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Mapping,
    Optional,
    Self,
    Sequence,
    cast,
)
from uuid import UUID

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.engine.row import Row

from ai.backend.manager.services.user.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.user.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
    UserModifier,
)
from ai.backend.manager.services.user.actions.purge_user import (
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.user.type import UserCreator, UserData, UserInfoContext
from ai.backend.manager.types import OptionalState, TriState

from ..base import (
    FilterExprArg,
    Item,
    OrderExprArg,
    PaginatedConnectionField,
    PaginatedList,
    batch_multiresult,
    batch_result,
    generate_sql_info_for_gql_connection,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult
from ..group import association_groups_users as agus
from ..group import groups
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from ..user import (
    ACTIVE_USER_STATUSES,
    INACTIVE_USER_STATUSES,
    UserRole,
    UserRow,
    UserStatus,
    users,
)

if TYPE_CHECKING:
    from ..gql import GraphQueryContext
    from .group import GroupNode


__all__ = (
    "UserNode",
    "UserConnection",
    "User",
    "UserGroup",
    "UserList",
    "UserInput",
    "ModifyUserInput",
    "PurgeUserInput",
    "CreateUser",
    "ModifyUser",
    "DeleteUser",
    "PurgeUser",
)


class UserNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    username = graphene.String(description="Unique username of the user.")
    email = graphene.String(description="Unique email of the user.")
    need_password_change = graphene.Boolean()
    full_name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean(
        deprecation_reason="Deprecated since 24.03.0. Recommend to use `status` field."
    )
    status = graphene.String(
        description="The status is one of `active`, `inactive`, `deleted` or `before-verification`."
    )
    status_info = graphene.String(description="Additional information of user status.")
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    domain_name = graphene.String()
    role = graphene.String(
        description="The role is one of `user`, `admin`, `superadmin` or `monitor`."
    )
    resource_policy = graphene.String()
    allowed_client_ip = graphene.List(lambda: graphene.String)
    totp_activated = graphene.Boolean()
    totp_activated_at = GQLDateTime()
    sudo_session_enabled = graphene.Boolean()
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

    project_nodes = PaginatedConnectionField(
        "ai.backend.manager.models.gql_models.group.GroupConnection",
        description="Added in 25.5.0.",
    )

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: UserRow) -> Self:
        return cls(
            id=row.uuid,
            username=row.username,
            email=row.email,
            need_password_change=row.need_password_change,
            full_name=row.full_name,
            description=row.description,
            is_active=(row.status == UserStatus.ACTIVE),
            status=row.status,
            status_info=row.status_info,
            created_at=row.created_at,
            modified_at=row.modified_at,
            domain_name=row.domain_name,
            role=row.role,
            resource_policy=row.resource_policy,
            allowed_client_ip=row.allowed_client_ip,
            totp_activated=row.totp_activated,
            totp_activated_at=row.totp_activated_at,
            sudo_session_enabled=row.sudo_session_enabled,
            container_uid=row.container_uid,
            container_main_gid=row.container_main_gid,
            container_gids=row.container_gids,
        )

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id) -> Self:
        graph_ctx: GraphQueryContext = info.context

        _, user_id = AsyncNode.resolve_global_id(info, id)
        query = sa.select(UserRow).where(UserRow.uuid == user_id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            user_row = (await db_session.scalars(query)).first()
            return cls.from_row(graph_ctx, user_row)

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "uuid": ("uuid", None),
        "username": ("username", None),
        "email": ("email", None),
        "need_password_change": ("need_password_change", None),
        "full_name": ("full_name", None),
        "description": ("description", None),
        "is_active": ("is_active", None),
        "status": ("status", UserStatus),
        "status_info": ("status_info", None),
        "created_at": ("created_at", dtparse),
        "modified_at": ("modified_at", dtparse),
        "domain_name": ("domain_name", None),
        "role": ("role", UserRole),
        "resource_policy": ("resource_policy", None),
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
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        filter_expr: str | None = None,
        order_expr: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult[Self]:
        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter_expr, QueryFilterParser(cls._queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(cls._queryorder_colmap))
            if order_expr is not None
            else None
        )
        (
            query,
            cnt_query,
            _,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            UserRow,
            UserRow.uuid,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            user_rows = (await db_session.scalars(query)).all()
            result = [cls.from_row(graph_ctx, row) for row in user_rows]
            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    async def resolve_project_nodes(
        self,
        info: graphene.ResolveInfo,
        filter: Optional[str] = None,
        order: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[GroupNode]:
        from ..group import AssocGroupUserRow, GroupRow
        from .group import GroupNode

        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter, QueryFilterParser(GroupNode.queryfilter_fieldspec))
            if filter is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order, QueryOrderParser(GroupNode.queryorder_colmap))
            if order is not None
            else None
        )
        (
            query,
            cnt_query,
            _,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            GroupRow,
            GroupRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        j = sa.join(GroupRow, AssocGroupUserRow)
        prj_query = query.select_from(j).where(AssocGroupUserRow.user_id == self.id)
        cnt_query = cnt_query.select_from(j).where(AssocGroupUserRow.user_id == self.id)
        result: list[GroupNode] = []
        async with graph_ctx.db.begin_readonly_session() as db_session:
            total_cnt = await db_session.scalar(cnt_query)
            async for row in await db_session.stream_scalars(prj_query):
                prj_row = cast(GroupRow, row)
                result.append(GroupNode.from_row(graph_ctx, prj_row))
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class UserConnection(Connection):
    class Meta:
        node = UserNode
        description = "Added in 24.03.0"


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
        "status": ("status", UserStatus),
        "status_info": ("status_info", None),
        "created_at": ("created_at", dtparse),
        "modified_at": ("modified_at", dtparse),
        "domain_name": ("domain_name", None),
        "role": ("role", UserRole),
        "resource_policy": ("resource_policy", None),
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
            input=UserCreator(
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
            ),
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
        return ModifyUserAction(
            email=email,
            modifier=UserModifier(
                username=OptionalState[str].from_graphql(
                    self.username,
                ),
                password=OptionalState[str].from_graphql(
                    self.password,
                ),
                need_password_change=OptionalState[bool].from_graphql(
                    self.need_password_change,
                ),
                full_name=OptionalState[str].from_graphql(
                    self.full_name,
                ),
                description=OptionalState[str].from_graphql(
                    self.description,
                ),
                is_active=OptionalState[bool].from_graphql(
                    self.is_active,
                ),
                status=OptionalState[UserStatus].from_graphql(
                    self.status
                    if (self.status is Undefined or self.status is None)
                    else UserStatus(self.status),
                ),
                domain_name=OptionalState[str].from_graphql(
                    self.domain_name,
                ),
                role=OptionalState[UserRole].from_graphql(
                    self.role
                    if (self.role is Undefined or self.role is None)
                    else UserRole(self.role),
                ),
                allowed_client_ip=TriState[list[str]].from_graphql(
                    self.allowed_client_ip,
                ),
                totp_activated=OptionalState[bool].from_graphql(
                    self.totp_activated,
                ),
                resource_policy=OptionalState[str].from_graphql(
                    self.resource_policy,
                ),
                sudo_session_enabled=OptionalState[bool].from_graphql(
                    self.sudo_session_enabled,
                ),
                main_access_key=TriState[str].from_graphql(
                    self.main_access_key,
                ),
                container_uid=TriState[int].from_graphql(
                    self.container_uid,
                ),
                container_main_gid=TriState[int].from_graphql(
                    self.container_main_gid,
                ),
                container_gids=TriState[list[int]].from_graphql(
                    self.container_gids,
                ),
            ),
            group_ids=OptionalState[list[str]].from_graphql(
                self.group_ids,
            ),
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
            purge_shared_vfolders=OptionalState[bool].from_graphql(
                self.purge_shared_vfolders,
            ),
            delegate_endpoint_ownership=OptionalState[bool].from_graphql(
                self.delegate_endpoint_ownership,
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
