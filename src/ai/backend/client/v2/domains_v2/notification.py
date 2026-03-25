"""V2 SDK client for the notification domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
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
from ai.backend.common.dto.manager.v2.notification.response import (
    CreateNotificationChannelPayload,
    CreateNotificationRulePayload,
    DeleteNotificationChannelPayload,
    DeleteNotificationRulePayload,
    GetNotificationChannelPayload,
    GetNotificationRulePayload,
    SearchNotificationChannelsPayload,
    SearchNotificationRulesPayload,
    UpdateNotificationChannelPayload,
    UpdateNotificationRulePayload,
    ValidateNotificationChannelPayload,
    ValidateNotificationRulePayload,
)

_PATH = "/v2/notifications"


class V2NotificationClient(BaseDomainClient):
    """SDK client for notification management (channels and rules)."""

    # ------------------------------------------------------------------ Channels

    async def create_channel(
        self, request: CreateNotificationChannelInput
    ) -> CreateNotificationChannelPayload:
        """Create a new notification channel."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/channels",
            request=request,
            response_model=CreateNotificationChannelPayload,
        )

    async def get_channel(self, channel_id: UUID) -> GetNotificationChannelPayload:
        """Retrieve a single notification channel by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/channels/{channel_id}",
            response_model=GetNotificationChannelPayload,
        )

    async def update_channel(
        self, channel_id: UUID, request: UpdateNotificationChannelInput
    ) -> UpdateNotificationChannelPayload:
        """Update an existing notification channel."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/channels/{channel_id}",
            request=request,
            response_model=UpdateNotificationChannelPayload,
        )

    async def delete_channel(
        self, request: DeleteNotificationChannelInput
    ) -> DeleteNotificationChannelPayload:
        """Delete a notification channel."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/channels/delete",
            request=request,
            response_model=DeleteNotificationChannelPayload,
        )

    async def search_channels(
        self, request: SearchNotificationChannelsInput
    ) -> SearchNotificationChannelsPayload:
        """Search notification channels with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/channels/search",
            request=request,
            response_model=SearchNotificationChannelsPayload,
        )

    async def validate_channel(
        self, request: ValidateNotificationChannelInput
    ) -> ValidateNotificationChannelPayload:
        """Validate a notification channel by sending a test message."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/channels/validate",
            request=request,
            response_model=ValidateNotificationChannelPayload,
        )

    # ------------------------------------------------------------------ Rules

    async def create_rule(
        self, request: CreateNotificationRuleInput
    ) -> CreateNotificationRulePayload:
        """Create a new notification rule."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/rules",
            request=request,
            response_model=CreateNotificationRulePayload,
        )

    async def get_rule(self, rule_id: UUID) -> GetNotificationRulePayload:
        """Retrieve a single notification rule by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/rules/{rule_id}",
            response_model=GetNotificationRulePayload,
        )

    async def update_rule(
        self, rule_id: UUID, request: UpdateNotificationRuleInput
    ) -> UpdateNotificationRulePayload:
        """Update an existing notification rule."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/rules/{rule_id}",
            request=request,
            response_model=UpdateNotificationRulePayload,
        )

    async def delete_rule(
        self, request: DeleteNotificationRuleInput
    ) -> DeleteNotificationRulePayload:
        """Delete a notification rule."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/rules/delete",
            request=request,
            response_model=DeleteNotificationRulePayload,
        )

    async def search_rules(
        self, request: SearchNotificationRulesInput
    ) -> SearchNotificationRulesPayload:
        """Search notification rules with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/rules/search",
            request=request,
            response_model=SearchNotificationRulesPayload,
        )

    async def validate_rule(
        self, request: ValidateNotificationRuleInput
    ) -> ValidateNotificationRulePayload:
        """Validate a notification rule by rendering its template with test data."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/rules/validate",
            request=request,
            response_model=ValidateNotificationRulePayload,
        )
