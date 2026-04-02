"""REST v2 handler for the notification domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.notification.request import (
    CreateNotificationChannelInput,
    CreateNotificationRuleInput,
    DeleteNotificationChannelInput,
    DeleteNotificationRuleInput,
    SearchNotificationChannelsInput,
    SearchNotificationRulesInput,
    UpdateNotificationChannelInput,
    UpdateNotificationRuleInput,
    ValidateNotificationChannelInput,
    ValidateNotificationRuleInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import ChannelIdPathParam, RuleIdPathParam
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.notification import NotificationAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2NotificationHandler:
    """REST v2 handler for notification operations (channels and rules)."""

    def __init__(self, *, adapter: NotificationAdapter) -> None:
        self._adapter = adapter

    # ------------------------------------------------------------------ channels

    async def create_channel(
        self,
        ctx: UserContext,
        body: BodyParam[CreateNotificationChannelInput],
    ) -> APIResponse:
        """Create a new notification channel."""
        result = await self._adapter.create_channel(body.parsed, created_by=ctx.user_uuid)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get_channel(
        self,
        path: PathParam[ChannelIdPathParam],
    ) -> APIResponse:
        """Retrieve a single notification channel by ID."""
        result = await self._adapter.get_channel(path.parsed.channel_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_channel(
        self,
        path: PathParam[ChannelIdPathParam],
        body: BodyParam[UpdateNotificationChannelInput],
    ) -> APIResponse:
        """Update an existing notification channel."""
        result = await self._adapter.update_channel(path.parsed.channel_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_channel(
        self,
        body: BodyParam[DeleteNotificationChannelInput],
    ) -> APIResponse:
        """Delete a notification channel."""
        result = await self._adapter.delete_channel(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_channels(
        self,
        body: BodyParam[SearchNotificationChannelsInput],
    ) -> APIResponse:
        """Search notification channels with filters, orders, and pagination."""
        result = await self._adapter.search_channels(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def validate_channel(
        self,
        body: BodyParam[ValidateNotificationChannelInput],
    ) -> APIResponse:
        """Validate a notification channel by sending a test message."""
        result = await self._adapter.validate_channel(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------ rules

    async def create_rule(
        self,
        ctx: UserContext,
        body: BodyParam[CreateNotificationRuleInput],
    ) -> APIResponse:
        """Create a new notification rule."""
        result = await self._adapter.create_rule(body.parsed, created_by=ctx.user_uuid)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get_rule(
        self,
        path: PathParam[RuleIdPathParam],
    ) -> APIResponse:
        """Retrieve a single notification rule by ID."""
        result = await self._adapter.get_rule(path.parsed.rule_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_rule(
        self,
        path: PathParam[RuleIdPathParam],
        body: BodyParam[UpdateNotificationRuleInput],
    ) -> APIResponse:
        """Update an existing notification rule."""
        result = await self._adapter.update_rule(path.parsed.rule_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_rule(
        self,
        body: BodyParam[DeleteNotificationRuleInput],
    ) -> APIResponse:
        """Delete a notification rule."""
        result = await self._adapter.delete_rule(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_rules(
        self,
        body: BodyParam[SearchNotificationRulesInput],
    ) -> APIResponse:
        """Search notification rules with filters, orders, and pagination."""
        result = await self._adapter.search_rules(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def validate_rule(
        self,
        body: BodyParam[ValidateNotificationRuleInput],
    ) -> APIResponse:
        """Validate a notification rule by rendering its template with test data."""
        result = await self._adapter.validate_rule(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
