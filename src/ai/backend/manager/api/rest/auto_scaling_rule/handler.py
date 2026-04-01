"""Auto-scaling rule handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``UserContext``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.scale import ModelDeploymentAutoScalingRuleCreator
from ai.backend.manager.dto.auto_scaling_rule_request import (
    GetAutoScalingRulePathParam,
    UpdateAutoScalingRulePathParam,
)
from ai.backend.manager.dto.context import UserContext
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

from .adapter import AutoScalingRuleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AutoScalingRuleHandler:
    """Auto-scaling rule API handler with constructor-injected dependencies."""

    def __init__(self, *, deployment: DeploymentProcessors) -> None:
        self._deployment = deployment
        self._adapter = AutoScalingRuleAdapter()

    async def create(
        self,
        body: BodyParam[CreateAutoScalingRuleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Create a new auto-scaling rule."""
        log.info("AUTO_SCALING_RULE.CREATE (ak:{})", ctx.access_key)

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

        action_result = await self._deployment.create_auto_scaling_rule.wait_for_complete(
            CreateAutoScalingRuleAction(creator=creator)
        )

        resp = CreateAutoScalingRuleResponse(
            auto_scaling_rule=self._adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def get(
        self,
        path: PathParam[GetAutoScalingRulePathParam],
        ctx: UserContext,
    ) -> APIResponse:
        """Get a specific auto-scaling rule."""
        log.info("AUTO_SCALING_RULE.GET (ak:{})", ctx.access_key)

        action_result = await self._deployment.get_auto_scaling_rule.wait_for_complete(
            GetAutoScalingRuleAction(auto_scaling_rule_id=path.parsed.rule_id)
        )

        resp = GetAutoScalingRuleResponse(
            auto_scaling_rule=self._adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search(
        self,
        body: BodyParam[SearchAutoScalingRulesRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search auto-scaling rules with filters, orders, and pagination."""
        log.info("AUTO_SCALING_RULE.SEARCH (ak:{})", ctx.access_key)

        querier = self._adapter.build_querier(body.parsed)

        action_result = await self._deployment.search_auto_scaling_rules.wait_for_complete(
            SearchAutoScalingRulesAction(querier=querier)
        )

        resp = SearchAutoScalingRulesResponse(
            auto_scaling_rules=[self._adapter.convert_to_dto(rule) for rule in action_result.data],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update(
        self,
        path: PathParam[UpdateAutoScalingRulePathParam],
        body: BodyParam[UpdateAutoScalingRuleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Update an existing auto-scaling rule."""
        log.info("AUTO_SCALING_RULE.UPDATE (ak:{})", ctx.access_key)

        rule_id = path.parsed.rule_id
        modifier = self._adapter.build_modifier(body.parsed)

        action_result = await self._deployment.update_auto_scaling_rule.wait_for_complete(
            UpdateAutoScalingRuleAction(
                auto_scaling_rule_id=rule_id,
                modifier=modifier,
            )
        )

        resp = UpdateAutoScalingRuleResponse(
            auto_scaling_rule=self._adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete(
        self,
        body: BodyParam[DeleteAutoScalingRuleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Delete an auto-scaling rule."""
        log.info("AUTO_SCALING_RULE.DELETE (ak:{})", ctx.access_key)

        action_result = await self._deployment.delete_auto_scaling_rule.wait_for_complete(
            DeleteAutoScalingRuleAction(auto_scaling_rule_id=body.parsed.rule_id)
        )

        resp = DeleteAutoScalingRuleResponse(deleted=action_result.success)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
