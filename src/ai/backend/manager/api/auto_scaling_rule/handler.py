"""
REST API handlers for auto-scaling rule system.
Provides CRUD endpoints for auto-scaling rules.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.dto.manager.auto_scaling_rule import (
    CreateAutoScalingRuleRequest,
    CreateAutoScalingRuleResponse,
    DeleteAutoScalingRuleRequest,
    DeleteAutoScalingRuleResponse,
    GetAutoScalingRuleResponse,
    PaginationInfo,
    SearchAutoScalingRulesRequest,
    SearchAutoScalingRulesResponse,
    UpdateAutoScalingRuleRequest,
    UpdateAutoScalingRuleResponse,
)
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.data.deployment.scale import ModelDeploymentAutoScalingRuleCreator
from ai.backend.manager.dto.auto_scaling_rule_request import (
    GetAutoScalingRulePathParam,
    UpdateAutoScalingRulePathParam,
)
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.get_auto_scaling_rule import (
    GetAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.search_auto_scaling_rules import (
    SearchAutoScalingRulesAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.update_auto_scaling_rule import (
    UpdateAutoScalingRuleAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.processors import Processors

from .adapter import AutoScalingRuleAdapter

__all__ = ("create_app",)


class AutoScalingRuleAPIHandler:
    """REST API handler class for auto-scaling rule operations."""

    def __init__(self) -> None:
        self.adapter = AutoScalingRuleAdapter()

    def _get_deployment_processors(self, processors: Processors) -> DeploymentProcessors:
        """Get deployment processors, raising ServiceUnavailable if not available."""
        if processors.deployment is None:
            raise web.HTTPServiceUnavailable(
                reason="Deployment service is not available on this manager"
            )
        return processors.deployment

    @auth_required_for_method
    @api_handler
    async def create(
        self,
        body: BodyParam[CreateAutoScalingRuleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new auto-scaling rule."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        creator = ModelDeploymentAutoScalingRuleCreator(
            model_deployment_id=body.parsed.model_deployment_id,
            metric_source=body.parsed.metric_source,
            metric_name=body.parsed.metric_name,
            min_threshold=body.parsed.min_threshold,
            max_threshold=body.parsed.max_threshold,
            step_size=body.parsed.step_size,
            time_window=body.parsed.time_window,
            min_replicas=body.parsed.min_replicas,
            max_replicas=body.parsed.max_replicas,
        )

        action_result = await deployment_processors.create_auto_scaling_rule.wait_for_complete(
            CreateAutoScalingRuleAction(creator=creator)
        )

        resp = CreateAutoScalingRuleResponse(
            auto_scaling_rule=self.adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetAutoScalingRulePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific auto-scaling rule."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        action_result = await deployment_processors.get_auto_scaling_rule.wait_for_complete(
            GetAutoScalingRuleAction(auto_scaling_rule_id=path.parsed.rule_id)
        )

        resp = GetAutoScalingRuleResponse(
            auto_scaling_rule=self.adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchAutoScalingRulesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search auto-scaling rules with filters, orders, and pagination."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        querier = self.adapter.build_querier(body.parsed)

        action_result = await deployment_processors.search_auto_scaling_rules.wait_for_complete(
            SearchAutoScalingRulesAction(querier=querier)
        )

        resp = SearchAutoScalingRulesResponse(
            auto_scaling_rules=[self.adapter.convert_to_dto(rule) for rule in action_result.data],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update(
        self,
        path: PathParam[UpdateAutoScalingRulePathParam],
        body: BodyParam[UpdateAutoScalingRuleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing auto-scaling rule."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        rule_id = path.parsed.rule_id
        modifier = self.adapter.build_modifier(body.parsed)

        action_result = await deployment_processors.update_auto_scaling_rule.wait_for_complete(
            UpdateAutoScalingRuleAction(
                auto_scaling_rule_id=rule_id,
                modifier=modifier,
            )
        )

        resp = UpdateAutoScalingRuleResponse(
            auto_scaling_rule=self.adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete(
        self,
        body: BodyParam[DeleteAutoScalingRuleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete an auto-scaling rule."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        action_result = await deployment_processors.delete_auto_scaling_rule.wait_for_complete(
            DeleteAutoScalingRuleAction(auto_scaling_rule_id=body.parsed.rule_id)
        )

        resp = DeleteAutoScalingRuleResponse(deleted=action_result.success)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for auto-scaling rule API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/auto-scaling-rules"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = AutoScalingRuleAPIHandler()

    cors.add(app.router.add_route("POST", "/", api_handler.create))
    cors.add(app.router.add_route("GET", "/{rule_id}", api_handler.get))
    cors.add(app.router.add_route("POST", "/search", api_handler.search))
    cors.add(app.router.add_route("PATCH", "/{rule_id}", api_handler.update))
    cors.add(app.router.add_route("POST", "/delete", api_handler.delete))

    return app, []
