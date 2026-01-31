from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, overload

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.common import (
    GenericForbidden,
    ObjectNotFound,
    ServerMisconfiguredError,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.minilang import FieldSpecItem, OrderSpecItem
from ai.backend.manager.models.minilang.ordering import QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser
from ai.backend.manager.models.network import NetworkRow
from ai.backend.manager.models.user import UserRole

from .base import (
    FilterExprArg,
    OrderExprArg,
    generate_sql_info_for_gql_connection,
    gql_mutation_wrapper,
    orm_set_if_set,
)
from .gql_relay import AsyncNode, Connection, ConnectionResolverResult

if TYPE_CHECKING:
    from .schema import GraphQueryContext


__all__ = (
    "CreateNetwork",
    "DeleteNetwork",
    "ModifyNetwork",
    "NetworkConnection",
    "NetworkNode",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class NetworkNode(graphene.ObjectType):  # type: ignore[misc]
    """Added in 24.12.0."""

    class Meta:
        interfaces = (AsyncNode,)

    row_id = graphene.UUID()
    name = graphene.String()
    ref_name = graphene.String()
    driver = graphene.String()
    project = graphene.UUID()
    domain_name = graphene.String()
    options = graphene.JSONString()
    created_at = GQLDateTime()
    updated_at = GQLDateTime()

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("id", uuid.UUID),
        "name": ("name", None),
        "ref_name": ("ref_name", None),
        "driver": ("driver", None),
        "project": ("project", uuid.UUID),
        "domain_name": ("domain_name", None),
        "created_at": ("created_at", dtparse),
        "updated_at": ("updated_at", dtparse),
        "options": ("options", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("id", None),
        "name": ("name", None),
        "ref_name": ("ref_name", None),
        "driver": ("driver", None),
        "project": ("project", None),
        "domain_name": ("domain_name", None),
        "created_at": ("created_at", None),
        "updated_at": ("updated_at", None),
    }

    @overload
    @classmethod
    def from_row(cls, row: NetworkRow) -> NetworkNode: ...

    @overload
    @classmethod
    def from_row(cls, row: None) -> None: ...

    @classmethod
    def from_row(cls, row: NetworkRow | None) -> NetworkNode | None:
        if row is None:
            return None
        return cls(
            id=row.id,
            row_id=row.id,
            name=row.name,
            ref_name=row.ref_name,
            driver=row.driver,
            project=row.project,
            domain_name=row.domain_name,
            options=row.options,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id: str) -> NetworkNode:
        graph_ctx: GraphQueryContext = info.context

        _, raw_network_id = AsyncNode.resolve_global_id(info, id)
        if not raw_network_id:
            raw_network_id = id

        async with graph_ctx.db.begin_readonly_session() as db_session:
            try:
                return cls.from_row(
                    await NetworkRow.get(db_session, uuid.UUID(raw_network_id), load_project=True)
                )
            except NoResultFound as e:
                raise ValueError(f"Network not found (id: {raw_network_id})") from e

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
    ) -> ConnectionResolverResult[NetworkNode]:
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
            NetworkRow,
            NetworkRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            additional_cond: sa.ColumnElement[bool]
            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    additional_cond = sa.true()
                case UserRole.ADMIN:
                    additional_cond = NetworkRow.domain_name == graph_ctx.user["domain_name"]
                case UserRole.USER:
                    project_query = sa.select(AssocGroupUserRow).where(
                        AssocGroupUserRow.user_id == graph_ctx.user["uuid"]
                    )
                    available_projects = (await db_session.execute(project_query)).scalars().all()
                    additional_cond = NetworkRow.project.in_([
                        p.group_id for p in available_projects
                    ])

            query = query.where(additional_cond)
            cnt_query = cnt_query.where(additional_cond)
            query = query.options(
                selectinload(NetworkRow.project_row),
                selectinload(NetworkRow.domain_row),
            )
            network_rows = (await db_session.scalars(query)).all()
            total_cnt = await db_session.scalar(cnt_query)
        result = []
        for network in network_rows:
            if (_node := cls.from_row(network)) is not None:
                result.append(_node)
            else:
                total_cnt -= 1
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class CreateNetwork(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.12.0."""

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        name = graphene.String(required=True)
        project_id = graphene.UUID(required=True)
        driver = graphene.String()

    ok = graphene.Boolean()
    msg = graphene.String()
    network = graphene.Field(NetworkNode)

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
        project_id: uuid.UUID,
        driver: str | None,
    ) -> CreateNetwork:
        graph_ctx: GraphQueryContext = info.context
        network_config = graph_ctx.config_provider.config.network.inter_container
        if network_config.enabled:
            return CreateNetwork(
                ok=False, msg="Inter-container networking disabled on this cluster", network=None
            )
        if not network_config.plugin:
            return CreateNetwork(ok=False, msg="No network plugin configured", network=None)
        _driver = network_config.default_driver
        if not _driver:
            return CreateNetwork(ok=False, msg="No network driver configured", network=None)

        async with graph_ctx.db.begin_readonly_session() as db_session:
            try:
                project = await GroupRow.get(db_session, project_id, load_resource_policy=True)
            except NoResultFound as e:
                raise ObjectNotFound(object_name="project") from e

            if (
                graph_ctx.user["role"] != UserRole.SUPERADMIN
                and project.domain_name != graph_ctx.user["domain_name"]
            ):
                raise GenericForbidden
            query = sa.select(sa.func.count("*")).where(NetworkRow.project == project.id)
            project_network_count = await db_session.scalar(query) or 0
            max_network_count = project.resource_policy_row.max_network_count
            if (
                max_network_count is not None
                and project_network_count >= 0
                and project_network_count >= max_network_count
            ):
                raise GenericForbidden(
                    "Cannot create more networks on this project (restricted by project resource policy)"
                )

        network_plugin = graph_ctx.network_plugin_ctx.plugins[_driver]
        try:
            network_info = await network_plugin.create_network()
            network_name = network_info.network_id
        except Exception:
            log.exception(f"Failed to create the inter-container network (plugin: {_driver})")
            raise

        async def _do_mutate() -> CreateNetwork:
            async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
                row = NetworkRow(
                    name,
                    network_name,
                    _driver,
                    project.domain_name,
                    project.id,
                    options=network_info.options,
                )
                db_session.add(row)
                return CreateNetwork(
                    ok=True,
                    msg="Network created",
                    network=NetworkNode.from_row(row),
                )

        return await gql_mutation_wrapper(CreateNetwork, _do_mutate)


class ModifyNetworkInput(graphene.InputObjectType):  # type: ignore[misc]
    """Added in 24.12.0."""

    name = graphene.String(required=True)


class ModifyNetwork(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.12.0."""

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        network = graphene.String(required=True)
        props = ModifyNetworkInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    network = graphene.Field(NetworkNode)

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        network: str,
        props: ModifyNetworkInput,
    ) -> ModifyNetwork:
        _, raw_network_id = AsyncNode.resolve_global_id(info, network)
        if not raw_network_id:
            raw_network_id = network

        try:
            _network_id = uuid.UUID(raw_network_id)
        except ValueError as e:
            raise ObjectNotFound("network") from e

        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await NetworkRow.get(db_session, _network_id, load_project=True)
            except NoResultFound as e:
                raise ObjectNotFound(object_name="network") from e

            if (
                graph_ctx.user["role"] != UserRole.SUPERADMIN
                and row.project_row.domain_name != graph_ctx.user["domain_name"]
            ):
                raise GenericForbidden

            async def _do_mutate() -> ModifyNetwork:
                orm_set_if_set(props, row, "name")
                row.updated_at = datetime.now(UTC)
                return ModifyNetwork(
                    ok=True,
                    msg="Network altered",
                    network=NetworkNode.from_row(row),
                )

            return await gql_mutation_wrapper(ModifyNetwork, _do_mutate)


class DeleteNetwork(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.12.0."""

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        network = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @staticmethod
    async def mutate(root: Any, info: graphene.ResolveInfo, network: str) -> DeleteNetwork:
        graph_ctx: GraphQueryContext = info.context

        _, raw_network_id = AsyncNode.resolve_global_id(info, network)
        if not raw_network_id:
            raw_network_id = network

        try:
            _network_id = uuid.UUID(raw_network_id)
        except ValueError as e:
            raise ObjectNotFound("network") from e

        async with graph_ctx.db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await NetworkRow.get(db_session, _network_id, load_project=True)
            except NoResultFound as e:
                raise ObjectNotFound(object_name="network") from e

            if (
                graph_ctx.user["role"] != UserRole.SUPERADMIN
                and row.project_row.domain_name != graph_ctx.user["domain_name"]
            ):
                raise GenericForbidden

            try:
                network_plugin = graph_ctx.network_plugin_ctx.plugins[row.driver]
            except KeyError as e:
                raise ServerMisconfiguredError(f"Network plugin {row.driver} not configured") from e
            await network_plugin.destroy_network(row.ref_name)

            async def _do_mutate() -> DeleteNetwork:
                update_query = sa.delete(NetworkRow).where(NetworkRow.id == _network_id)
                await db_session.execute(update_query)
                return DeleteNetwork(ok=True, msg="Network deleted")

            return await gql_mutation_wrapper(DeleteNetwork, _do_mutate)


class NetworkConnection(Connection):  # type: ignore[misc]
    """Added in 24.12.0."""

    class Meta:
        node = NetworkNode
        description = "Added in 24.12.0."
