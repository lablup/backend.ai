"""Admin handler class using constructor dependency injection.

Handles GraphQL endpoints (graphene legacy, graphene v1, strawberry v2).
The Strawberry GraphQL view is registered separately since it uses its own
class-based handler (``CustomGraphQLView``).
"""

from __future__ import annotations

import logging
import traceback
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final, cast

import graphene
from graphene.validation import depth_limit_validator
from graphql import ValidationRule, parse, validate
from graphql.error import GraphQLError
from graphql.execution import ExecutionResult

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.admin.request import GraphQLRequest
from ai.backend.common.dto.manager.admin.response import GraphQLResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api.gql_legacy.base import DataLoaderManager
from ai.backend.manager.api.gql_legacy.schema import (
    GQLExceptionMiddleware,
    GQLMetricMiddleware,
    GQLMutationPrivilegeCheckMiddleware,
    GraphQueryContext,
)
from ai.backend.manager.api.rest.types import GQLContextDeps
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import GraphQLError as BackendGQLError
from ai.backend.manager.errors.common import ServerFrozen

if TYPE_CHECKING:
    from graphql import FieldNode

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GQLMutationUnfrozenRequiredMiddleware:
    """GraphQL middleware that blocks mutations when the manager is frozen."""

    def __init__(self, manager_status: ManagerStatus) -> None:
        self._manager_status = manager_status

    def resolve(self, next: Any, root: Any, info: graphene.ResolveInfo, **args: Any) -> Any:
        if info.operation.operation == "mutation" and self._manager_status == ManagerStatus.FROZEN:
            raise ServerFrozen
        return next(root, info, **args)


class GQLLoggingMiddleware:
    def resolve(self, next: Any, root: Any, info: graphene.ResolveInfo, **args: Any) -> Any:
        if info.path.prev is None:
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
    def enter_field(self, node: FieldNode, *_args: Any) -> None:
        field_name = node.name.value
        if field_name.startswith("__"):
            if field_name == "__typename":
                return
            self.report_error(
                GraphQLError(f"Cannot query '{field_name}': introspection is disabled.", node)
            )


class AdminHandler:
    """Admin API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        gql_schema: graphene.Schema,
        gql_deps: GQLContextDeps,
    ) -> None:
        self._gql_schema = gql_schema
        self._gql_deps = gql_deps

    async def _handle_gql_common(
        self, request_ctx: RequestCtx, params: GraphQLRequest
    ) -> ExecutionResult:
        request = request_ctx.request
        gql_deps = self._gql_deps
        manager_status = (
            await gql_deps.config_provider.legacy_etcd_config_loader.get_manager_status()
        )
        known_slot_types = (
            await gql_deps.config_provider.legacy_etcd_config_loader.get_resource_slots()
        )
        rules: list[type[ValidationRule]] = []
        if not gql_deps.config_provider.config.api.allow_graphql_schema_introspection:
            rules.append(CustomIntrospectionRule)
        max_depth = gql_deps.config_provider.config.api.max_gql_query_depth
        if max_depth is not None:
            rules.append(depth_limit_validator(max_depth=max_depth))
        if rules:
            validate_errors = validate(
                schema=self._gql_schema.graphql_schema,
                document_ast=parse(params.query),
                rules=rules,
            )
            if validate_errors:
                return ExecutionResult(None, errors=validate_errors)
        gql_ctx = GraphQueryContext(
            schema=self._gql_schema,
            dataloader_manager=DataLoaderManager(),
            config_provider=gql_deps.config_provider,
            etcd=gql_deps.etcd,
            user=request["user"],
            access_key=request["keypair"]["access_key"],
            db=gql_deps.db,
            valkey_stat=gql_deps.valkey_stat,
            valkey_image=gql_deps.valkey_image,
            valkey_live=gql_deps.valkey_live,
            valkey_schedule=gql_deps.valkey_schedule,
            network_plugin_ctx=gql_deps.network_plugin_ctx,
            manager_status=manager_status,
            known_slot_types=known_slot_types,
            background_task_manager=gql_deps.background_task_manager,
            services_ctx=gql_deps.services_ctx,
            storage_manager=gql_deps.storage_manager,
            registry=gql_deps.registry,
            idle_checker_host=gql_deps.idle_checker_host,
            metric_observer=gql_deps.metric_observer,
            processors=gql_deps.processors,
            scheduler_repository=gql_deps.scheduler_repository,
            user_repository=gql_deps.user_repository,
            agent_repository=gql_deps.agent_repository,
        )
        result = cast(
            ExecutionResult,
            await self._gql_schema.execute_async(
                params.query,
                None,
                variable_values=params.variables,
                operation_name=params.operation_name,
                context_value=gql_ctx,
                middleware=[
                    GQLMutationPrivilegeCheckMiddleware(),
                    GQLMutationUnfrozenRequiredMiddleware(manager_status),
                    GQLMetricMiddleware(),
                    GQLExceptionMiddleware(),
                    GQLLoggingMiddleware(),
                ],
            ),
        )
        if result.errors:
            for e in result.errors:
                log.error("ADMIN.GQL Exception: {}", e.formatted)
                log.debug("{}", "".join(traceback.format_exception(e)))
        return result

    # ------------------------------------------------------------------
    # handle_gql_graphene (POST /admin/gql)
    # ------------------------------------------------------------------

    async def handle_gql_graphene(
        self,
        body: BodyParam[GraphQLRequest],
        ctx: UserContext,
        request_ctx: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        result = await self._handle_gql_common(request_ctx, params)
        resp = GraphQLResponse(
            data=result.data,
            errors=[dict(e.formatted) for e in result.errors] if result.errors else None,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # handle_gql_legacy (POST /admin/graphql)
    # ------------------------------------------------------------------

    async def handle_gql_legacy(
        self,
        body: BodyParam[GraphQLRequest],
        ctx: UserContext,
        request_ctx: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        result = await self._handle_gql_common(request_ctx, params)
        if result.errors:
            errors = []
            for e in result.errors:
                errors.append(e.formatted)
                log.error("ADMIN.GQL Exception: {}", e.formatted)
            raise BackendGQLError(extra_data=errors)
        resp = GraphQLResponse(data=result.data)
        return APIResponse.build(HTTPStatus.OK, resp)
