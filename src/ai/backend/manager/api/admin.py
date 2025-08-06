from __future__ import annotations

import logging
import traceback
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Iterable, Optional, Self, Tuple, cast

import aiohttp_cors
import attrs
import graphene
import strawberry
import trafaret as t
from aiohttp import web
from graphene.validation import DisableIntrospection, depth_limit_validator
from graphql import parse, validate
from graphql.error import GraphQLError  # pants: no-infer-dep
from graphql.execution import ExecutionResult  # pants: no-infer-dep
from pydantic import ConfigDict, Field

from ai.backend.common import validators as tx
from ai.backend.common.api_handlers import APIResponse, BodyParam, MiddlewareParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.request import GraphQLReq
from ai.backend.common.dto.manager.response import GraphQLResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from ..api.gql.schema import schema as strawberry_schema
from ..errors.api import GraphQLError as BackendGQLError
from ..models.base import DataLoaderManager
from ..models.gql import (
    GQLExceptionMiddleware,
    GQLMetricMiddleware,
    GQLMutationPrivilegeCheckMiddleware,
    GraphQueryContext,
    Mutations,
    Queries,
)
from .auth import auth_required, auth_required_for_method
from .manager import GQLMutationUnfrozenRequiredMiddleware
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GQLLoggingMiddleware:
    def resolve(self, next, root, info: graphene.ResolveInfo, **args) -> Any:
        if info.path.prev is None:  # indicates the root query
            graph_ctx = info.context
            log.info(
                "ADMIN.GQL (ak:{}, {}:{}, op:{})",
                graph_ctx.access_key,
                info.operation.operation,
                info.field_name,
                info.operation.name,
            )
        return next(root, info, **args)


async def _handle_gql_common(request: web.Request, params: Any) -> ExecutionResult:
    root_ctx: RootContext = request.app["_root.context"]
    app_ctx: PrivateContext = request.app["admin.context"]
    manager_status = await root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status()
    known_slot_types = await root_ctx.config_provider.legacy_etcd_config_loader.get_resource_slots()
    rules = []
    if not root_ctx.config_provider.config.api.allow_graphql_schema_introspection:
        rules.append(DisableIntrospection)
    max_depth = cast(int | None, root_ctx.config_provider.config.api.max_gql_query_depth)
    if max_depth is not None:
        rules.append(depth_limit_validator(max_depth=max_depth))
    if rules:
        validate_errors = validate(
            schema=app_ctx.gql_schema.graphql_schema,
            document_ast=parse(params["query"]),
            rules=rules,
        )
        if validate_errors:
            return ExecutionResult(None, errors=validate_errors)
    gql_ctx = GraphQueryContext(
        schema=app_ctx.gql_schema,
        dataloader_manager=DataLoaderManager(),
        config_provider=root_ctx.config_provider,
        etcd=root_ctx.etcd,
        user=request["user"],
        access_key=request["keypair"]["access_key"],
        db=root_ctx.db,
        valkey_stat=root_ctx.valkey_stat,
        valkey_image=root_ctx.valkey_image,
        valkey_live=root_ctx.valkey_live,
        network_plugin_ctx=root_ctx.network_plugin_ctx,
        manager_status=manager_status,
        known_slot_types=known_slot_types,
        background_task_manager=root_ctx.background_task_manager,
        services_ctx=root_ctx.services_ctx,
        storage_manager=root_ctx.storage_manager,
        registry=root_ctx.registry,
        idle_checker_host=root_ctx.idle_checker_host,
        metric_observer=root_ctx.metrics.gql,
        processors=root_ctx.processors,
    )
    result = await app_ctx.gql_schema.execute_async(
        params["query"],
        None,  # root
        variable_values=params["variables"],
        operation_name=params["operation_name"],
        context_value=gql_ctx,
        middleware=[
            GQLMutationPrivilegeCheckMiddleware(),
            GQLMutationUnfrozenRequiredMiddleware(),
            GQLMetricMiddleware(),
            GQLExceptionMiddleware(),
            GQLLoggingMiddleware(),
        ],
    )

    if result.errors:
        for e in result.errors:
            if isinstance(e, GraphQLError):
                errmsg = e.formatted
            else:
                errmsg = {"message": str(e)}
            log.error("ADMIN.GQL Exception: {}", errmsg)
            log.debug("{}", "".join(traceback.format_exception(e)))
    return result


@auth_required
@check_api_params(
    t.Dict({
        t.Key("query"): t.String,
        t.Key("variables", default=None): t.Null | t.Mapping(t.String, t.Any),
        tx.AliasedKey(["operation_name", "operationName"], default=None): t.Null | t.String,
    })
)
async def handle_gql(request: web.Request, params: Any) -> web.Response:
    result = await _handle_gql_common(request, params)
    return web.json_response(result.formatted, status=HTTPStatus.OK)


class GQLInspectionConfigCtx(MiddlewareParam):
    gql_v2_schema: strawberry.Schema = Field(
        ..., description="Strawberry GraphQL schema for v2 API."
    )
    allow_graphql_schema_introspection: bool
    max_gql_query_depth: Optional[int]

    # Allow strawberry.Schema to be used as a type
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]
        app_ctx: PrivateContext = request.app["admin.context"]

        return cls(
            gql_v2_schema=app_ctx.gql_v2_schema,
            allow_graphql_schema_introspection=root_ctx.config_provider.config.api.allow_graphql_schema_introspection,
            max_gql_query_depth=root_ctx.config_provider.config.api.max_gql_query_depth,
        )


class V2APIHandler:
    @auth_required_for_method
    @api_handler
    async def handle_gql_v2(
        self,
        body: BodyParam[GraphQLReq],
        config_ctx: GQLInspectionConfigCtx,
    ) -> APIResponse:
        rules = []

        if not config_ctx.allow_graphql_schema_introspection:
            rules.append(DisableIntrospection)
        max_depth = cast(int | None, config_ctx.max_gql_query_depth)
        if max_depth is not None:
            rules.append(depth_limit_validator(max_depth=max_depth))

        if rules:
            validate_errors = validate(
                # TODO: Instead of accessing private field, use another approach
                schema=config_ctx.gql_v2_schema._schema,
                document_ast=parse(body.parsed.query),
                rules=rules,
            )
            if validate_errors:
                validation_result = ExecutionResult(None, errors=validate_errors)
                return APIResponse.build(
                    status_code=HTTPStatus.BAD_REQUEST,
                    response_model=GraphQLResponse(
                        data=None, errors=validation_result.formatted.get("errors", [])
                    ),
                )

        user = current_user()
        if not user:
            raise web.HTTPUnauthorized(
                text="Unauthorized: User identity is required for GraphQL v2 API."
            )

        strawberry_ctx = StrawberryGQLContext(
            user=user,
        )

        query, variables, operation_name = (
            body.parsed.query,
            body.parsed.variables,
            body.parsed.operation_name,
        )

        result = await config_ctx.gql_v2_schema.execute(
            query,
            root_value=None,
            variable_values=variables,
            operation_name=operation_name,
            context_value=strawberry_ctx,
        )

        errors = []
        if result.errors:
            for err in result.errors:
                log.error("ADMIN.GQL-V2 Exception: {}", err.formatted)
                errors.append(err.formatted)

        response_data = GraphQLResponse(
            data=result.data, errors=errors, extensions=result.extensions
        )
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response_data,
        )


@auth_required
@check_api_params(
    t.Dict({
        t.Key("query"): t.String,
        t.Key("variables", default=None): t.Null | t.Mapping(t.String, t.Any),
        tx.AliasedKey(["operation_name", "operationName"], default=None): t.Null | t.String,
    })
)
async def handle_gql_legacy(request: web.Request, params: Any) -> web.Response:
    # FIXME: remove in v21.09
    result = await _handle_gql_common(request, params)
    if result.errors:
        errors = []
        for e in result.errors:
            if isinstance(e, GraphQLError):
                errmsg = e.formatted
                errors.append(errmsg)
            else:
                errmsg = {"message": str(e)}
                errors.append(errmsg)
            log.error("ADMIN.GQL Exception: {}", errmsg)
        raise BackendGQLError(extra_data=errors)
    return web.json_response(result.data, status=HTTPStatus.OK)


@attrs.define(auto_attribs=True, slots=True, init=False)
class PrivateContext:
    gql_schema: graphene.Schema
    gql_v2_schema: strawberry.Schema


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["admin.context"]
    app_ctx.gql_schema = graphene.Schema(
        query=Queries,
        mutation=Mutations,
        auto_camelcase=False,
    )
    app_ctx.gql_v2_schema = strawberry_schema
    root_ctx: RootContext = app["_root.context"]
    if root_ctx.config_provider.config.api.allow_graphql_schema_introspection:
        log.warning(
            "GraphQL schema introspection is enabled. "
            "It is strongly advised to disable this in production setups."
        )


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["admin.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", r"/graphql", handle_gql_legacy))
    cors.add(app.router.add_route("POST", r"/gql", handle_gql))

    v2_api_handler = V2APIHandler()
    cors.add(app.router.add_route("POST", r"/gql/v2", v2_api_handler.handle_gql_v2))
    return app, []
