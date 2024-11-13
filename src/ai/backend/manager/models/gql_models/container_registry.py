from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional, Self, cast

import aiohttp
import graphene
import graphql
import sqlalchemy as sa
import yarl
from graphql import Undefined, UndefinedType
from sqlalchemy.orm import load_only

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.logging_utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import ContainerRegistryNotFound
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.gql_models.fields import ScopeField
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.rbac import (
    ContainerRegistryScope,
    ProjectScope,
    ScopeType,
    SystemScope,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from ...defs import PASSWORD_PLACEHOLDER
from ..base import (
    FilterExprArg,
    OrderExprArg,
    PaginatedConnectionField,
    generate_sql_info_for_gql_connection,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from .group import GroupConnection, GroupNode

if TYPE_CHECKING:
    from ..gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = (
    "AllowedGroups",
    "ContainerRegistryNode",
    "ContainerRegistryConnection",
    "ContainerRegistryScopeField",
    "ContainerRegistryTypeField",
    "CreateContainerRegistryNode",
    "ModifyContainerRegistryNode",
    "DeleteContainerRegistryNode",
)


class ContainerRegistryTypeField(graphene.Scalar):
    """Added in 24.09.0."""

    allowed_values = tuple(t.value for t in ContainerRegistryType)

    @staticmethod
    def serialize(val: ContainerRegistryType) -> str:
        return val.value

    @staticmethod
    def parse_literal(node, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return ContainerRegistryType(node.value)

    @staticmethod
    def parse_value(value: str) -> ContainerRegistryType:
        return ContainerRegistryType(value)


class ContainerRegistryNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.09.0."

    row_id = graphene.UUID(
        description="Added in 24.09.0. The UUID type id of DB container_registries row."
    )
    name = graphene.String()
    url = graphene.String(required=True, description="Added in 24.09.0.")
    type = ContainerRegistryTypeField(required=True, description="Added in 24.09.0.")
    registry_name = graphene.String(required=True, description="Added in 24.09.0.")
    is_global = graphene.Boolean(description="Added in 24.09.0.")
    project = graphene.String(description="Added in 24.09.0.")
    username = graphene.String(description="Added in 24.09.0.")
    password = graphene.String(description="Added in 24.09.0.")
    ssl_verify = graphene.Boolean(description="Added in 24.09.0.")
    extra = graphene.JSONString(description="Added in 24.09.3.")
    allowed_groups = PaginatedConnectionField(GroupConnection, description="Added in 25.3.0.")

    _queryfilter_fieldspec: dict[str, FieldSpecItem] = {
        "row_id": ("id", None),
        "registry_name": ("registry_name", None),
    }
    _queryorder_colmap: dict[str, OrderSpecItem] = {
        "row_id": ("id", None),
        "registry_name": ("registry_name", None),
    }

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id: str) -> ContainerRegistryNode:
        graph_ctx: GraphQueryContext = info.context
        _, reg_id = AsyncNode.resolve_global_id(info, id)
        select_stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            reg_row = cast(ContainerRegistryRow | None, await db_session.scalar(select_stmt))
            if reg_row is None:
                raise ValueError(f"Container registry not found (id: {reg_id})")
            return cls.from_row(graph_ctx, reg_row)

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
    ) -> ConnectionResolverResult:
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
            ContainerRegistryRow,
            ContainerRegistryRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            reg_rows = await db_session.scalars(query)
            total_cnt = await db_session.scalar(cnt_query)
        result = [cls.from_row(graph_ctx, cast(ContainerRegistryRow, row)) for row in reg_rows]
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: ContainerRegistryRow) -> ContainerRegistryNode:
        return cls(
            id=row.id,  # auto-converted to Relay global ID
            row_id=row.id,
            url=row.url,
            type=row.type,
            registry_name=row.registry_name,
            project=row.project,
            username=row.username,
            password=PASSWORD_PLACEHOLDER if row.password is not None else None,
            ssl_verify=row.ssl_verify,
            is_global=row.is_global,
            extra=row.extra,
        )

    async def resolve_allowed_groups(
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
        scope = SystemScope()

        if self.is_global:
            container_registry_scope = None
        else:
            container_registry_scope = ContainerRegistryScope.parse(f"container_registry:{self.id}")

        return await GroupNode.get_connection(
            info,
            scope,
            container_registry_scope,
            filter_expr=filter,
            order_expr=order,
            offset=offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )


class ContainerRegistryConnection(Connection):
    """Added in 25.3.0."""

    class Meta:
        node = ContainerRegistryNode
        description = "Added in 24.09.0."


class ContainerRegistryScopeField(graphene.Scalar):
    class Meta:
        description = "Added in 25.3.0."

    @staticmethod
    def serialize(val: ContainerRegistryScope) -> str:
        if isinstance(val, ContainerRegistryScope):
            return str(val)
        raise ValueError("Invalid ContainerRegistryScope")

    @staticmethod
    def parse_value(value):
        if isinstance(value, str):
            try:
                return ContainerRegistryScope.parse(value)
            except Exception as e:
                raise ValueError(f"Invalid ContainerRegistryScope: {e}")
        raise ValueError("Invalid ContainerRegistryScope")

    @staticmethod
    def parse_literal(node):
        if isinstance(node, graphql.language.ast.StringValueNode):
            try:
                return ContainerRegistryScope.parse(node.value)
            except Exception as e:
                raise ValueError(f"Invalid ContainerRegistryScope: {e}")
        return None


class AllowedGroups(graphene.InputObjectType):
    """
    Added in 25.3.0.
    """

    add = graphene.List(
        graphene.String,
        default_value=[],
        description="List of group_ids to add associations. Added in 25.3.0.",
    )
    remove = graphene.List(
        graphene.String,
        default_value=[],
        description="List of group_ids to remove associations. Added in 25.3.0.",
    )


async def handle_allowed_groups_update(
    db: ExtendedAsyncSAEngine,
    registry_id: uuid.UUID,
    allowed_group_updates: AllowedGroups | AllowedGroupsModel,
):
    async with db.begin_session() as db_sess:
        if allowed_group_updates.add:
            insert_values = [
                {"registry_id": registry_id, "group_id": group_id}
                for group_id in allowed_group_updates.add
            ]

            insert_query = sa.insert(AssociationContainerRegistriesGroupsRow).values(insert_values)
            await db_sess.execute(insert_query)

        if allowed_group_updates.remove:
            delete_query = (
                sa.delete(AssociationContainerRegistriesGroupsRow)
                .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
                .where(
                    AssociationContainerRegistriesGroupsRow.group_id.in_(
                        allowed_group_updates.remove
                    )
                )
            )
            result = await db_sess.execute(delete_query)
            if result.rowcount == 0:
                raise ContainerRegistryNotFound()


class CreateContainerRegistryNode(graphene.Mutation):
    """
    Deprecated since 25.3.0. use `CreateContainerRegistryNodeV2` instead
    """

    class Meta:
        description = "Added in 24.09.0."

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistryNode)

    class Arguments:
        url = graphene.String(required=True, description="Added in 24.09.0.")
        type = ContainerRegistryTypeField(
            required=True,
            description=f"Added in 24.09.0. Registry type. One of {ContainerRegistryTypeField.allowed_values}.",
        )
        registry_name = graphene.String(required=True, description="Added in 24.09.0.")
        is_global = graphene.Boolean(description="Added in 24.09.0.")
        project = graphene.String(description="Added in 24.09.0.")
        username = graphene.String(description="Added in 24.09.0.")
        password = graphene.String(description="Added in 24.09.0.")
        ssl_verify = graphene.Boolean(description="Added in 24.09.0.")
        extra = graphene.JSONString(description="Added in 24.09.3.")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        url: str,
        type: ContainerRegistryType,
        registry_name: str,
        is_global: bool | UndefinedType = Undefined,
        project: str | UndefinedType = Undefined,
        username: str | UndefinedType = Undefined,
        password: str | UndefinedType = Undefined,
        ssl_verify: bool | UndefinedType = Undefined,
        extra: dict | UndefinedType = Undefined,
    ) -> CreateContainerRegistryNode:
        ctx: GraphQueryContext = info.context

        input_config: dict[str, Any] = {
            "registry_name": registry_name,
            "url": url,
            "type": type,
        }

        def _set_if_set(name: str, val: Any) -> None:
            if val is not Undefined:
                input_config[name] = val

        _set_if_set("project", project)
        _set_if_set("username", username)
        _set_if_set("password", password)
        _set_if_set("ssl_verify", ssl_verify)
        _set_if_set("is_global", is_global)
        _set_if_set("extra", extra)

        async with ctx.db.begin_session() as db_session:
            reg_row = ContainerRegistryRow(**input_config)
            db_session.add(reg_row)
            await db_session.flush()
            await db_session.refresh(reg_row)

            return cls(
                container_registry=ContainerRegistryNode.from_row(ctx, reg_row),
            )


class ModifyContainerRegistryNode(graphene.Mutation):
    """
    Deprecated since 25.3.0. use `ModifyContainerRegistryNodeV2` instead
    """

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistryNode)

    class Meta:
        description = "Added in 24.09.0."

    class Arguments:
        id = graphene.String(
            required=True,
            description="Object id. Can be either global id or object id. Added in 24.09.0.",
        )
        url = graphene.String(description="Added in 24.09.0.")
        type = ContainerRegistryTypeField(
            description=f"Registry type. One of {ContainerRegistryTypeField.allowed_values}. Added in 24.09.0."
        )
        registry_name = graphene.String(description="Added in 24.09.0.")
        is_global = graphene.Boolean(description="Added in 24.09.0.")
        project = graphene.String(description="Added in 24.09.0.")
        username = graphene.String(description="Added in 24.09.0.")
        password = graphene.String(description="Added in 24.09.0.")
        ssl_verify = graphene.Boolean(description="Added in 24.09.0.")
        extra = graphene.JSONString(description="Added in 24.09.3.")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
        url: str | UndefinedType = Undefined,
        type: ContainerRegistryType | UndefinedType = Undefined,
        registry_name: str | UndefinedType = Undefined,
        is_global: bool | UndefinedType = Undefined,
        project: str | UndefinedType = Undefined,
        username: str | UndefinedType = Undefined,
        password: str | UndefinedType = Undefined,
        ssl_verify: bool | UndefinedType = Undefined,
        extra: dict | UndefinedType = Undefined,
    ) -> ModifyContainerRegistryNode:
        ctx: GraphQueryContext = info.context

        input_config: dict[str, Any] = {}

        def _set_if_set(name: str, val: Any) -> None:
            if val is not Undefined:
                input_config[name] = val

        _set_if_set("url", url)
        _set_if_set("type", type)
        _set_if_set("registry_name", registry_name)
        _set_if_set("username", username)
        _set_if_set("password", password)
        _set_if_set("project", project)
        _set_if_set("ssl_verify", ssl_verify)
        _set_if_set("is_global", is_global)
        _set_if_set("extra", extra)

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)

        async with ctx.db.begin_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
            reg_row = await session.scalar(stmt)
            if reg_row is None:
                raise ValueError(f"ContainerRegistry not found (id: {reg_id})")
            for field, val in input_config.items():
                setattr(reg_row, field, val)

            return cls(container_registry=ContainerRegistryNode.from_row(ctx, reg_row))


class DeleteContainerRegistryNode(graphene.Mutation):
    """
    Deprecated since 25.3.0. use `DeleteContainerRegistryNodeV2` instead
    """

    allowed_roles = (UserRole.SUPERADMIN,)
    container_registry = graphene.Field(ContainerRegistryNode)

    class Meta:
        description = "Added in 24.09.0."

    class Arguments:
        id = graphene.String(
            required=True,
            description="Object id. Can be either global id or object id. Added in 24.09.0.",
        )

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        id: str,
    ) -> DeleteContainerRegistryNode:
        ctx: GraphQueryContext = info.context

        _, _id = AsyncNode.resolve_global_id(info, id)
        reg_id = uuid.UUID(_id) if _id else uuid.UUID(id)
        async with ctx.db.begin_session() as db_session:
            reg_row = await ContainerRegistryRow.get(db_session, reg_id)
            reg_row = await db_session.scalar(
                sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
            )
            if reg_row is None:
                raise ValueError(f"Container registry not found (id:{reg_id})")
            container_registry = ContainerRegistryNode.from_row(ctx, reg_row)
            await db_session.execute(
                sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == reg_id)
            )

        return cls(container_registry=container_registry)


class UpdateQuota(graphene.Mutation):
    """Added in 24.12.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        scope_id = ScopeField(required=True)
        quota = graphene.Int(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
        quota: int,
    ) -> Self:
        if not isinstance(scope_id, ProjectScope):
            return UpdateQuota(
                ok=False, msg="Quota mutation currently supports only the project scope."
            )

        project_id = scope_id.project_id
        graph_ctx = info.context

        async with graph_ctx.db.begin_session() as db_sess:
            group_query = (
                sa.select(GroupRow)
                .where(GroupRow.id == project_id)
                .options(load_only(GroupRow.container_registry))
            )
            result = await db_sess.execute(group_query)
            group_row = result.scalar_one_or_none()

            if (
                not group_row
                or not group_row.container_registry
                or "registry" not in group_row.container_registry
                or "project" not in group_row.container_registry
            ):
                return UpdateQuota(
                    ok=False,
                    msg=f"Container registry info does not exist in the group. (gr: {project_id})",
                )

            registry_name, project = (
                group_row.container_registry["registry"],
                group_row.container_registry["project"],
            )

            registry_query = sa.select(ContainerRegistryRow).where(
                (ContainerRegistryRow.registry_name == registry_name)
                & (ContainerRegistryRow.project == project)
            )

            result = await db_sess.execute(registry_query)
            registry = result.scalars().one_or_none()

            if not registry:
                return UpdateQuota(
                    ok=False,
                    msg=f"Specified container registry row does not exist. (cr: {registry_name}, gr: {project})",
                )

            if registry.type != ContainerRegistryType.HARBOR2:
                return UpdateQuota(ok=False, msg="Only HarborV2 registry is supported for now.")

        ssl_verify = registry.ssl_verify
        connector = aiohttp.TCPConnector(ssl=ssl_verify)

        api_url = yarl.URL(registry.url) / "api" / "v2.0"
        async with aiohttp.ClientSession(connector=connector) as sess:
            rqst_args: dict[str, Any] = {}
            rqst_args["auth"] = aiohttp.BasicAuth(
                registry.username,
                registry.password,
            )

            get_project_id_api = api_url / "projects" / project

            async with sess.get(get_project_id_api, allow_redirects=False, **rqst_args) as resp:
                res = await resp.json()
                harbor_project_id = res["project_id"]

                get_quota_id_api = (api_url / "quotas").with_query({
                    "reference": "project",
                    "reference_id": harbor_project_id,
                })

            async with sess.get(get_quota_id_api, allow_redirects=False, **rqst_args) as resp:
                res = await resp.json()
                if not res:
                    return UpdateQuota(
                        ok=False, msg=f"Quota entity not found. (project_id: {harbor_project_id})"
                    )
                if len(res) > 1:
                    return UpdateQuota(
                        ok=False,
                        msg=f"Multiple quota entity found. (project_id: {harbor_project_id})",
                    )

                quota_id = res[0]["id"]

                put_quota_api = api_url / "quotas" / str(quota_id)
                payload = {"hard": {"storage": quota}}

            async with sess.put(
                put_quota_api, json=payload, allow_redirects=False, **rqst_args
            ) as resp:
                if resp.status == 200:
                    return UpdateQuota(ok=True, msg="Quota updated successfully.")
                else:
                    log.error(f"Failed to update quota: {await resp.json()}")
                    return UpdateQuota(
                        ok=False, msg=f"Failed to update quota. Status code: {resp.status}"
                    )

        return UpdateQuota(ok=False, msg="Unknown error!")
