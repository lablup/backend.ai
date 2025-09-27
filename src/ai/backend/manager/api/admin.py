from __future__ import annotations

import json
import logging
import traceback
from enum import Enum
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterable, Optional, Self, Tuple, cast

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
from pydantic import BaseModel, ConfigDict, Field

from ai.backend.common import validators as tx
from ai.backend.common.api_handlers import APIResponse, BodyParam, MiddlewareParam, api_handler
from ai.backend.common.dto.manager.request import GraphQLReq
from ai.backend.common.dto.manager.response import GraphQLResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dto.context import ProcessorsCtx

from ..api.gql.schema import schema as strawberry_schema
from ..errors.api import GraphQLError as BackendGQLError
from ..models.base import DataLoaderManager
from ..models.gql import (
    GQLExceptionMiddleware,
    GQLMetricMiddleware,
    GQLMutationPrivilegeCheckMiddleware,
    GraphQueryContext,
    Mutation,
    Query,
)
from .auth import auth_required, auth_required_for_method
from .manager import GQLMutationUnfrozenRequiredMiddleware
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from graphql import FieldNode

    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# WebSocket message type enum
class GraphQLWSMessageType(str, Enum):
    CONNECTION_INIT = "connection_init"
    SUBSCRIBE = "subscribe"
    COMPLETE = "complete"


# Payload types for WebSocket messages
class GraphQLWSSubscribePayload(BaseModel):
    query: str
    variables: dict[str, Any] | None = None
    operationName: str | None = None


# Union type for all WebSocket messages
class GraphQLWSMessage(BaseModel):
    type: GraphQLWSMessageType
    id: str | None = None
    payload: dict[str, Any] | None = None  # Will be validated in specific message types


# Type for schema.subscribe return value - it returns either an AsyncIterator of ExecutionResult
# or a single ExecutionResult for non-subscription operations
SubscriptionResult = AsyncIterator[ExecutionResult]


# WebSocket response message types
class GraphQLWSConnectionAck(BaseModel):
    type: str = "connection_ack"


class GraphQLWSNext(BaseModel):
    type: str = "next"
    id: str
    payload: dict[str, Any]


class GraphQLWSError(BaseModel):
    type: str = "error"
    id: str | None = None
    payload: list[dict[str, str]]


class GraphQLWSCompleteResponse(BaseModel):
    type: str = "complete"
    id: str


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


class ConfigProviderCtx(MiddlewareParam):
    config_provider: ManagerConfigProvider

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]

        return cls(
            config_provider=root_ctx.config_provider,
        )


class GQLAPIHandler:
    @auth_required_for_method
    @api_handler
    async def handle_gql_strawberry(
        self,
        body: BodyParam[GraphQLReq],
        gql_config_ctx: GQLInspectionConfigCtx,
        config_provider_ctx: ConfigProviderCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        rules = []

        if not gql_config_ctx.allow_graphql_schema_introspection:
            rules.append(CustomIntrospectionRule)
        max_depth = cast(int | None, gql_config_ctx.max_gql_query_depth)
        if max_depth is not None:
            rules.append(depth_limit_validator(max_depth=max_depth))

        if rules:
            validate_errors = validate(
                # TODO: Instead of accessing private field, use another approach
                schema=gql_config_ctx.gql_v2_schema._schema,
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

        strawberry_ctx = StrawberryGQLContext(
            processors=processors_ctx.processors,
            config_provider=config_provider_ctx.config_provider,
            event_hub=processors_ctx.event_hub,
            event_fetcher=processors_ctx.event_fetcher,
            valkey_bgtask=processors_ctx.valkey_bgtask,
        )

        query, variables, operation_name = (
            body.parsed.query,
            body.parsed.variables,
            body.parsed.operation_name,
        )

        result = await gql_config_ctx.gql_v2_schema.execute(
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
        query=Query,
        mutation=Mutation,
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


@auth_required
async def handle_gql_strawberry_ws(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(protocols=["graphql-transport-ws", "graphql-ws"])
    await ws.prepare(request)

    root_ctx: RootContext = request.app["_root.context"]
    processors_ctx = await ProcessorsCtx.from_request(request)
    context = StrawberryGQLContext(
        processors=processors_ctx.processors,
        config_provider=root_ctx.config_provider,
        event_hub=processors_ctx.event_hub,
        event_fetcher=processors_ctx.event_fetcher,
        valkey_bgtask=processors_ctx.valkey_bgtask,
    )

    schema = request.app["admin.context"].gql_v2_schema

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                # Parse and validate WebSocket message using Pydantic
                raw_data = msg.json()
                ws_message = GraphQLWSMessage.model_validate(raw_data)

                if ws_message.type == GraphQLWSMessageType.CONNECTION_INIT:
                    response = GraphQLWSConnectionAck()
                    await ws.send_str(json.dumps(response.model_dump()))

                elif ws_message.type == GraphQLWSMessageType.SUBSCRIBE:
                    if not ws_message.id or not ws_message.payload:
                        raise ValueError("Subscribe message requires id and payload")

                    # Validate and parse subscription payload
                    subscribe_payload = GraphQLWSSubscribePayload.model_validate(ws_message.payload)
                    query = subscribe_payload.query
                    variables = subscribe_payload.variables or {}

                    log.info(
                        "Processing subscription: {}, query: {}, variables: {}",
                        ws_message.id,
                        query[:30],
                        variables,
                    )

                    try:
                        # Execute subscription using Strawberry's subscribe method
                        async_result: SubscriptionResult = await schema.subscribe(
                            query,
                            variable_values=variables,
                            context_value=context,
                        )

                        log.info("Subscription subscribe result: {}", type(async_result))

                        if not hasattr(async_result, "__aiter__"):
                            # TODO: Add exception
                            raise ValueError("Expected an async iterator for subscription")

                        log.info("Processing subscription async generator")

                        async for result in async_result:
                            log.info(
                                "Subscription result: errors={}, data={}",
                                result.errors,
                                result.data,
                            )

                            if result.errors:
                                log.error("Subscription errors: {}", result.errors)
                                error_response = GraphQLWSError(
                                    id=ws_message.id,
                                    payload=[{"message": str(e)} for e in result.errors],
                                )
                                await ws.send_str(json.dumps(error_response.model_dump()))
                                break
                            elif result.data:
                                log.info("Sending subscription data: {}", result.data)
                                next_response = GraphQLWSNext(
                                    id=ws_message.id, payload={"data": result.data}
                                )
                                await ws.send_str(json.dumps(next_response.model_dump()))

                        # Send completion after async iterator is exhausted
                        log.info("Subscription completed, sending complete message")
                        complete_response = GraphQLWSCompleteResponse(id=ws_message.id)
                        await ws.send_str(json.dumps(complete_response.model_dump()))

                    except Exception as e:
                        log.error("Subscription execution error: {}", e)
                        log.exception("Full traceback:")
                        error_response = GraphQLWSError(
                            id=ws_message.id, payload=[{"message": str(e)}]
                        )
                        await ws.send_str(json.dumps(error_response.model_dump()))

                elif ws_message.type == GraphQLWSMessageType.COMPLETE:
                    if not ws_message.id:
                        raise ValueError("Complete message requires id")
                    log.info("Received complete message for subscription: {}", ws_message.id)

            except Exception as e:
                # Handle message parsing and validation errors
                log.error("WebSocket message validation error: {}", e)
                error_response = GraphQLWSError(
                    payload=[{"message": f"Invalid message format: {str(e)}"}]
                )
                await ws.send_str(json.dumps(error_response.model_dump()))

    return ws


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

    gql_api_handler = GQLAPIHandler()
    cors.add(
        app.router.add_route("POST", r"/gql/strawberry", gql_api_handler.handle_gql_strawberry)
    )
    cors.add(app.router.add_get(r"/gql/strawberry/ws", handle_gql_strawberry_ws))

    return app, []
