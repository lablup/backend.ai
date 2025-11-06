"""
REST API handlers for notification system.
Provides CRUD endpoints for notification channels and rules.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    QueryParam,
    api_handler,
)
from ai.backend.common.contexts.user import current_user
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.notification_request import (
    CreateNotificationChannelReq,
    CreateNotificationRuleReq,
    DeleteNotificationChannelPathParam,
    DeleteNotificationRulePathParam,
    GetNotificationChannelPathParam,
    GetNotificationRulePathParam,
    ListNotificationChannelsReq,
    ListNotificationRulesReq,
    UpdateNotificationChannelBodyParam,
    UpdateNotificationChannelPathParam,
    UpdateNotificationRuleBodyParam,
    UpdateNotificationRulePathParam,
)
from ai.backend.manager.dto.notification_response import (
    CreateNotificationChannelResponse,
    CreateNotificationRuleResponse,
    DeleteNotificationChannelResponse,
    DeleteNotificationRuleResponse,
    GetNotificationChannelResponse,
    GetNotificationRuleResponse,
    ListNotificationChannelsResponse,
    ListNotificationRulesResponse,
    NotificationChannelDTO,
    NotificationRuleDTO,
    UpdateNotificationChannelResponse,
    UpdateNotificationRuleResponse,
)
from ai.backend.manager.repositories.base import Querier
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationRuleConditions,
)
from ai.backend.manager.services.notification.actions import (
    CreateChannelAction,
    CreateRuleAction,
    DeleteChannelAction,
    DeleteRuleAction,
    GetChannelAction,
    GetRuleAction,
    ListChannelsAction,
    ListRulesAction,
    UpdateChannelAction,
    UpdateRuleAction,
)

from ..data.notification import NotificationChannelCreator, NotificationRuleCreator
from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

__all__ = ("create_app",)


class NotificationAPIHandler:
    """REST API handler class for notification operations."""

    # Notification Channel Endpoints

    @auth_required_for_method
    @api_handler
    async def create_channel(
        self,
        body: BodyParam[CreateNotificationChannelReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new notification channel."""
        processors = processors_ctx.processors
        me = current_user()
        assert me is not None

        # Convert request to creator
        creator = NotificationChannelCreator(
            name=body.parsed.name,
            description=body.parsed.description,
            channel_type=body.parsed.channel_type,
            config=body.parsed.config,
            enabled=body.parsed.enabled,
            created_by=me.user_id,
        )

        # Call service action
        action_result = await processors.notification.create_channel.wait_for_complete(
            CreateChannelAction(creator=creator)
        )

        # Build response
        resp = CreateNotificationChannelResponse(
            channel=NotificationChannelDTO.from_data(action_result.channel_data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def list_channels(
        self,
        query: QueryParam[ListNotificationChannelsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """List all notification channels."""
        processors = processors_ctx.processors

        # Build querier from query parameters
        conditions = []
        if query.parsed.enabled_only:
            conditions.append(NotificationChannelConditions.by_enabled(True))

        querier = Querier(conditions=conditions, orders=[])

        # Call service action
        action_result = await processors.notification.list_channels.wait_for_complete(
            ListChannelsAction(querier=querier)
        )

        # Build response
        resp = ListNotificationChannelsResponse(
            channels=[NotificationChannelDTO.from_data(ch) for ch in action_result.channels]
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_channel(
        self,
        path: PathParam[GetNotificationChannelPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific notification channel."""
        processors = processors_ctx.processors

        # Call service action
        action_result = await processors.notification.get_channel.wait_for_complete(
            GetChannelAction(channel_id=path.parsed.channel_id)
        )

        # Build response
        resp = GetNotificationChannelResponse(
            channel=NotificationChannelDTO.from_data(action_result.channel_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_channel(
        self,
        path: PathParam[UpdateNotificationChannelPathParam],
        body: BodyParam[UpdateNotificationChannelBodyParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing notification channel."""
        processors = processors_ctx.processors

        # Call service action
        action_result = await processors.notification.update_channel.wait_for_complete(
            UpdateChannelAction(
                channel_id=path.parsed.channel_id,
                modifier=body.parsed.to_modifier(),
            )
        )

        # Build response
        resp = UpdateNotificationChannelResponse(
            channel=NotificationChannelDTO.from_data(action_result.channel_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete_channel(
        self,
        path: PathParam[DeleteNotificationChannelPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a notification channel."""
        processors = processors_ctx.processors

        # Call service action
        action_result = await processors.notification.delete_channel.wait_for_complete(
            DeleteChannelAction(channel_id=path.parsed.channel_id)
        )

        # Build response
        resp = DeleteNotificationChannelResponse(deleted=action_result.deleted)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Notification Rule Endpoints

    @auth_required_for_method
    @api_handler
    async def create_rule(
        self,
        body: BodyParam[CreateNotificationRuleReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new notification rule."""
        processors = processors_ctx.processors
        me = current_user()
        assert me is not None

        # Convert request to creator
        creator = NotificationRuleCreator(
            name=body.parsed.name,
            description=body.parsed.description,
            rule_type=body.parsed.rule_type,
            channel_id=body.parsed.channel_id,
            message_template=body.parsed.message_template,
            enabled=body.parsed.enabled,
            created_by=me.user_id,
        )

        # Call service action
        action_result = await processors.notification.create_rule.wait_for_complete(
            CreateRuleAction(creator=creator)
        )

        # Build response
        resp = CreateNotificationRuleResponse(
            rule=NotificationRuleDTO.from_data(action_result.rule_data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def list_rules(
        self,
        query: QueryParam[ListNotificationRulesReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """List all notification rules."""
        processors = processors_ctx.processors

        # Build querier from query parameters
        conditions = []
        if query.parsed.enabled_only:
            conditions.append(NotificationRuleConditions.by_enabled(True))
        if query.parsed.rule_type is not None:
            conditions.append(NotificationRuleConditions.by_rule_types([query.parsed.rule_type]))

        querier = Querier(conditions=conditions, orders=[])

        # Call service action
        action_result = await processors.notification.list_rules.wait_for_complete(
            ListRulesAction(querier=querier)
        )

        # Build response
        resp = ListNotificationRulesResponse(
            rules=[NotificationRuleDTO.from_data(rule) for rule in action_result.rules]
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_rule(
        self,
        path: PathParam[GetNotificationRulePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific notification rule."""
        processors = processors_ctx.processors

        # Call service action
        action_result = await processors.notification.get_rule.wait_for_complete(
            GetRuleAction(rule_id=path.parsed.rule_id)
        )

        # Build response
        resp = GetNotificationRuleResponse(
            rule=NotificationRuleDTO.from_data(action_result.rule_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_rule(
        self,
        path: PathParam[UpdateNotificationRulePathParam],
        body: BodyParam[UpdateNotificationRuleBodyParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing notification rule."""
        processors = processors_ctx.processors

        # Call service action
        action_result = await processors.notification.update_rule.wait_for_complete(
            UpdateRuleAction(
                rule_id=path.parsed.rule_id,
                modifier=body.parsed.to_modifier(),
            )
        )

        # Build response
        resp = UpdateNotificationRuleResponse(
            rule=NotificationRuleDTO.from_data(action_result.rule_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete_rule(
        self,
        path: PathParam[DeleteNotificationRulePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a notification rule."""
        processors = processors_ctx.processors

        # Call service action
        action_result = await processors.notification.delete_rule.wait_for_complete(
            DeleteRuleAction(rule_id=path.parsed.rule_id)
        )

        # Build response
        resp = DeleteNotificationRuleResponse(deleted=action_result.deleted)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for notification API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "notifications"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = NotificationAPIHandler()

    # Channel routes
    cors.add(app.router.add_route("POST", "/channels", api_handler.create_channel))
    cors.add(app.router.add_route("GET", "/channels", api_handler.list_channels))
    cors.add(app.router.add_route("GET", "/channels/{channel_id}", api_handler.get_channel))
    cors.add(app.router.add_route("PATCH", "/channels/{channel_id}", api_handler.update_channel))
    cors.add(app.router.add_route("DELETE", "/channels/{channel_id}", api_handler.delete_channel))

    # Rule routes
    cors.add(app.router.add_route("POST", "/rules", api_handler.create_rule))
    cors.add(app.router.add_route("GET", "/rules", api_handler.list_rules))
    cors.add(app.router.add_route("GET", "/rules/{rule_id}", api_handler.get_rule))
    cors.add(app.router.add_route("PATCH", "/rules/{rule_id}", api_handler.update_rule))
    cors.add(app.router.add_route("DELETE", "/rules/{rule_id}", api_handler.delete_rule))

    return app, []
