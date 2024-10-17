from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Mapping,
    Self,
)

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime

from ..base import (
    FilterExprArg,
    OrderExprArg,
    generate_sql_info_for_gql_connection,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser, enum_field_getter
from ..user import UserRole, UserRow, UserStatus

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


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
        "status": ("status", enum_field_getter(UserStatus)),
        "status_info": ("status_info", None),
        "created_at": ("created_at", dtparse),
        "modified_at": ("modified_at", dtparse),
        "domain_name": ("domain_name", None),
        "role": ("role", enum_field_getter(UserRole)),
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


class UserConnection(Connection):
    class Meta:
        node = UserNode
        description = "Added in 24.03.0"
