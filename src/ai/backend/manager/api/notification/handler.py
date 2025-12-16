"""
REST API handlers for notification system.
Provides CRUD endpoints for notification channels and rules.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.notification import (
    CreateNotificationChannelRequest,
    CreateNotificationChannelResponse,
    CreateNotificationRuleRequest,
    CreateNotificationRuleResponse,
    DeleteNotificationChannelResponse,
    DeleteNotificationRuleResponse,
    GetNotificationChannelResponse,
    GetNotificationRuleResponse,
    ListNotificationChannelsResponse,
    ListNotificationRulesResponse,
    ListNotificationRuleTypesResponse,
    NotificationRuleType,
    NotificationRuleTypeSchemaResponse,
    PaginationInfo,
    SearchNotificationChannelsRequest,
    SearchNotificationRulesRequest,
    UpdateNotificationChannelRequest,
    UpdateNotificationChannelResponse,
    UpdateNotificationRuleRequest,
    UpdateNotificationRuleResponse,
    ValidateNotificationChannelRequest,
    ValidateNotificationChannelResponse,
    ValidateNotificationRuleRequest,
    ValidateNotificationRuleResponse,
)
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.notification_request import (
    DeleteNotificationChannelPathParam,
    DeleteNotificationRulePathParam,
    GetNotificationChannelPathParam,
    GetNotificationRulePathParam,
    RuleTypePathParam,
    UpdateNotificationChannelPathParam,
    UpdateNotificationRulePathParam,
    ValidateNotificationChannelPathParam,
    ValidateNotificationRulePathParam,
)
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.notification.creators import (
    NotificationChannelCreatorSpec,
    NotificationRuleCreatorSpec,
)
from ai.backend.manager.services.notification.actions import (
    CreateChannelAction,
    CreateRuleAction,
    DeleteChannelAction,
    DeleteRuleAction,
    GetChannelAction,
    GetRuleAction,
    SearchChannelsAction,
    SearchRulesAction,
    UpdateChannelAction,
    UpdateRuleAction,
    ValidateChannelAction,
    ValidateRuleAction,
)

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware
from .adapter import NotificationChannelAdapter, NotificationRuleAdapter

__all__ = ("create_app",)


class NotificationAPIHandler:
    """REST API handler class for notification operations."""

    def __init__(self) -> None:
        self.channel_adapter = NotificationChannelAdapter()
        self.rule_adapter = NotificationRuleAdapter()

    # Notification Channel Endpoints

    @auth_required_for_method
    @api_handler
    async def create_channel(
        self,
        body: BodyParam[CreateNotificationChannelRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new notification channel."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can create notification channels.")

        # Convert request to creator
        # config validator in request DTO ensures this is WebhookConfig

        creator = Creator(
            spec=NotificationChannelCreatorSpec(
                name=body.parsed.name,
                description=body.parsed.description,
                channel_type=body.parsed.channel_type,
                config=body.parsed.config,
                enabled=body.parsed.enabled,
                created_by=me.user_id,
            )
        )

        # Call service action
        action_result = await processors.notification.create_channel.wait_for_complete(
            CreateChannelAction(creator=creator)
        )

        # Build response
        resp = CreateNotificationChannelResponse(
            channel=self.channel_adapter.convert_to_dto(action_result.channel_data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_channels(
        self,
        body: BodyParam[SearchNotificationChannelsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search notification channels with filters, orders, and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can search notification channels.")

        # Build querier using adapter
        querier = self.channel_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await processors.notification.search_channels.wait_for_complete(
            SearchChannelsAction(querier=querier)
        )

        # Build response
        resp = ListNotificationChannelsResponse(
            channels=[self.channel_adapter.convert_to_dto(ch) for ch in action_result.channels],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset or 0,
                limit=body.parsed.limit,
            ),
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
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can get notification channels.")

        # Call service action
        action_result = await processors.notification.get_channel.wait_for_complete(
            GetChannelAction(channel_id=path.parsed.channel_id)
        )

        # Build response
        resp = GetNotificationChannelResponse(
            channel=self.channel_adapter.convert_to_dto(action_result.channel_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_channel(
        self,
        path: PathParam[UpdateNotificationChannelPathParam],
        body: BodyParam[UpdateNotificationChannelRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing notification channel."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can update notification channels.")

        # Call service action
        channel_id = path.parsed.channel_id
        action_result = await processors.notification.update_channel.wait_for_complete(
            UpdateChannelAction(updater=self.channel_adapter.build_updater(body.parsed, channel_id))
        )

        # Build response
        resp = UpdateNotificationChannelResponse(
            channel=self.channel_adapter.convert_to_dto(action_result.channel_data)
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
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can delete notification channels.")

        # Call service action
        action_result = await processors.notification.delete_channel.wait_for_complete(
            DeleteChannelAction(channel_id=path.parsed.channel_id)
        )

        # Build response
        resp = DeleteNotificationChannelResponse(deleted=action_result.deleted)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def validate_channel(
        self,
        path: PathParam[ValidateNotificationChannelPathParam],
        body: BodyParam[ValidateNotificationChannelRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Validate a notification channel by sending a test webhook."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can validate notification channels.")

        # Call service action
        await processors.notification.validate_channel.wait_for_complete(
            ValidateChannelAction(
                channel_id=path.parsed.channel_id,
                test_message=body.parsed.test_message,
            )
        )

        # Build response
        resp = ValidateNotificationChannelResponse(
            channel_id=path.parsed.channel_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def validate_rule(
        self,
        path: PathParam[ValidateNotificationRulePathParam],
        body: BodyParam[ValidateNotificationRuleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Validate a notification rule by rendering its template with test data."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can validate notification rules.")

        # Service layer handles rule fetching and data validation
        action_result = await processors.notification.validate_rule.wait_for_complete(
            ValidateRuleAction(
                rule_id=path.parsed.rule_id,
                notification_data=body.parsed.notification_data,
            )
        )

        # Build response
        resp = ValidateNotificationRuleResponse(
            message=action_result.message,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def list_rule_types(
        self,
    ) -> APIResponse:
        """List all available notification rule types."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can list notification rule types.")

        # Return all available rule types from the enum
        resp = ListNotificationRuleTypesResponse(rule_types=list(NotificationRuleType))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_rule_type_schema(
        self,
        path: PathParam[RuleTypePathParam],
    ) -> APIResponse:
        """Get JSON schema for a notification rule type's message format."""
        from ai.backend.common.data.notification import NotifiableMessage

        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(
                reason="Only superadmin can view notification rule type schemas."
            )

        # Get schema for the requested rule type
        schema = NotifiableMessage.get_message_schema(path.parsed.rule_type)

        resp = NotificationRuleTypeSchemaResponse(
            rule_type=path.parsed.rule_type,
            json_schema=schema,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Notification Rule Endpoints

    @auth_required_for_method
    @api_handler
    async def create_rule(
        self,
        body: BodyParam[CreateNotificationRuleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new notification rule."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can create notification rules.")

        # Convert request to creator
        creator = Creator(
            spec=NotificationRuleCreatorSpec(
                name=body.parsed.name,
                description=body.parsed.description,
                rule_type=body.parsed.rule_type,
                channel_id=body.parsed.channel_id,
                message_template=body.parsed.message_template,
                enabled=body.parsed.enabled,
                created_by=me.user_id,
            )
        )

        # Call service action
        action_result = await processors.notification.create_rule.wait_for_complete(
            CreateRuleAction(creator=creator)
        )

        # Build response
        resp = CreateNotificationRuleResponse(
            rule=self.rule_adapter.convert_to_dto(action_result.rule_data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_rules(
        self,
        body: BodyParam[SearchNotificationRulesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search notification rules with filters, orders, and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can search notification rules.")

        # Build querier using adapter
        querier = self.rule_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await processors.notification.search_rules.wait_for_complete(
            SearchRulesAction(querier=querier)
        )

        # Build response
        resp = ListNotificationRulesResponse(
            rules=[self.rule_adapter.convert_to_dto(rule) for rule in action_result.rules],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset or 0,
                limit=body.parsed.limit,
            ),
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
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can get notification rules.")

        # Call service action
        action_result = await processors.notification.get_rule.wait_for_complete(
            GetRuleAction(rule_id=path.parsed.rule_id)
        )

        # Build response
        resp = GetNotificationRuleResponse(
            rule=self.rule_adapter.convert_to_dto(action_result.rule_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_rule(
        self,
        path: PathParam[UpdateNotificationRulePathParam],
        body: BodyParam[UpdateNotificationRuleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing notification rule."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can update notification rules.")

        # Call service action
        rule_id = path.parsed.rule_id
        action_result = await processors.notification.update_rule.wait_for_complete(
            UpdateRuleAction(updater=self.rule_adapter.build_updater(body.parsed, rule_id))
        )

        # Build response
        resp = UpdateNotificationRuleResponse(
            rule=self.rule_adapter.convert_to_dto(action_result.rule_data)
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
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can delete notification rules.")

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
    cors.add(app.router.add_route("POST", "/channels/search", api_handler.search_channels))
    cors.add(app.router.add_route("GET", "/channels/{channel_id}", api_handler.get_channel))
    cors.add(app.router.add_route("PATCH", "/channels/{channel_id}", api_handler.update_channel))
    cors.add(app.router.add_route("DELETE", "/channels/{channel_id}", api_handler.delete_channel))
    cors.add(
        app.router.add_route(
            "POST", "/channels/{channel_id}/validate", api_handler.validate_channel
        )
    )

    # Rule routes
    cors.add(app.router.add_route("GET", "/rule-types", api_handler.list_rule_types))
    cors.add(
        app.router.add_route(
            "GET", "/rule-types/{rule_type}/schema", api_handler.get_rule_type_schema
        )
    )
    cors.add(app.router.add_route("POST", "/rules", api_handler.create_rule))
    cors.add(app.router.add_route("POST", "/rules/search", api_handler.search_rules))
    cors.add(app.router.add_route("GET", "/rules/{rule_id}", api_handler.get_rule))
    cors.add(app.router.add_route("PATCH", "/rules/{rule_id}", api_handler.update_rule))
    cors.add(app.router.add_route("DELETE", "/rules/{rule_id}", api_handler.delete_rule))
    cors.add(app.router.add_route("POST", "/rules/{rule_id}/validate", api_handler.validate_rule))

    return app, []
