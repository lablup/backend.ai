from __future__ import annotations

import logging
import traceback
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Iterable, Tuple, cast

import aiohttp_cors
import attrs
import graphene
import strawberry
import trafaret as t
from aiohttp import web
from graphene.validation import depth_limit_validator
from graphql import ValidationRule, parse, validate
from graphql.error import GraphQLError  # pants: no-infer-dep
from graphql.execution import ExecutionResult  # pants: no-infer-dep
from strawberry.aiohttp.views import GraphQLView

from ai.backend.common import validators as tx
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.api.gql.data_loader.registry import DataLoaderRegistry
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.auth import AuthorizationFailed

from ..api.gql.schema import schema as strawberry_schema
from ..errors.api import GraphQLError as BackendGQLError
from ..models.base import DataLoaderManager
from ..models.gql import (
    GQLExceptionMiddleware,
    GQLMetricMiddleware,
    GQLMutationPrivilegeCheckMiddleware,
    GraphQueryContext,
    graphene_schema,
)
from .auth import auth_required
from .manager import GQLMutationUnfrozenRequiredMiddleware
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params, set_handler_attr

if TYPE_CHECKING:
    from graphql import FieldNode

    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class CustomGraphQLView(GraphQLView):
    """Custom GraphQL view for Backend.AI with OpenAPI compatibility."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__name__ = "handle_graphql_strawberry"
        self.__doc__ = """
        GraphQL endpoint using Strawberry schema.

        Supports both query/mutation via POST and subscriptions via WebSocket.
        """
        # Set handler attributes for middleware compatibility
        set_handler_attr(self, "auth_required", True)
        set_handler_attr(self, "auth_scope", "user")

    async def __call__(self, request: web.Request) -> web.StreamResponse:
        if request.get("is_authorized", False):
            return await super().__call__(request)
        raise AuthorizationFailed("Unauthorized access to GraphQL endpoint")

    async def get_context(  # type: ignore[override]
        self, request: web.Request, response: web.Response | web.WebSocketResponse
    ) -> StrawberryGQLContext:
        root_context: RootContext = request.app["_root.context"]
        return StrawberryGQLContext(
            processors=root_context.processors,
            config_provider=root_context.config_provider,
            event_hub=root_context.event_hub,
            event_fetcher=root_context.event_fetcher,
            dataloader_registry=DataLoaderRegistry(),  # TODO: Remove this.
            gql_adapter=root_context.gql_adapter,
            data_loaders=DataLoaders(root_context.processors),
        )


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


class CustomIntrospectionRule(ValidationRule):
    def enter_field(self, node: FieldNode, *_args):
        field_name = node.name.value
        if field_name.startswith("__"):
            # Allow __typename field for GraphQL Federation, @connection directive
            if field_name == "__typename":
                return
            self.report_error(
                GraphQLError(f"Cannot query '{field_name}': introspection is disabled.", node)
            )


async def _handle_gql_common(request: web.Request, params: Any) -> ExecutionResult:
    root_ctx: RootContext = request.app["_root.context"]
    app_ctx: PrivateContext = request.app["admin.context"]
    manager_status = await root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status()
    known_slot_types = await root_ctx.config_provider.legacy_etcd_config_loader.get_resource_slots()
    rules = []
    if not root_ctx.config_provider.config.api.allow_graphql_schema_introspection:
        rules.append(CustomIntrospectionRule)
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
        valkey_schedule=root_ctx.valkey_schedule,
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
        scheduler_repository=root_ctx.repositories.scheduler.repository,
        user_repository=root_ctx.repositories.user.repository,
        agent_repository=root_ctx.repositories.agent.repository,
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
async def handle_gql_graphene(request: web.Request, params: Any) -> web.Response:
    result = await _handle_gql_common(request, params)
    return web.json_response(result.formatted, status=HTTPStatus.OK)


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
    app_ctx.gql_schema = graphene_schema
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
    cors.add(app.router.add_route("POST", r"/gql", handle_gql_graphene))

    # Use CustomGraphQLView for strawberry schema with subscription support
    gql_view = CustomGraphQLView(schema=strawberry_schema, graphiql=False)
    cors.add(app.router.add_route("GET", r"/gql/strawberry", gql_view))
    cors.add(app.router.add_route("POST", r"/gql/strawberry", gql_view))
    return app, []
