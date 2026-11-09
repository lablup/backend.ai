"""V2 SDK client for the notification domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.notification.request import (
    CreateNotificationChannelInput,
    CreateNotificationRuleInput,
    DeleteNotificationChannelInput,
    DeleteNotificationRuleInput,
    PartialBulkPurgeNotificationChannelsInput,
    PartialBulkPurgeNotificationRulesInput,
    PartialBulkUpdateNotificationChannelsInput,
    PartialBulkUpdateNotificationRulesInput,
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
    NotificationChannelNode,
    NotificationRuleNode,
    PurgeNotificationChannelPayload,
    PurgeNotificationRulePayload,
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

    async def purge_channel(self, channel_id: UUID) -> PurgeNotificationChannelPayload:
        """Permanently remove a notification channel."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/channels/{channel_id}",
            response_model=PurgeNotificationChannelPayload,
        )

    async def partial_bulk_update_channels(
        self, request: PartialBulkUpdateNotificationChannelsInput
    ) -> PartialBulkPayload[NotificationChannelNode]:
        """Update several notification channels, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/channels/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[NotificationChannelNode],
        )

    async def partial_bulk_purge_channels(
        self, request: PartialBulkPurgeNotificationChannelsInput
    ) -> PartialBulkPayload[NotificationChannelNode]:
        """Permanently remove several notification channels, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/channels/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPayload[NotificationChannelNode],
        )

    async def delete_channel(
        self, request: DeleteNotificationChannelInput
    ) -> DeleteNotificationChannelPayload:
        """Deprecated. Use :meth:`purge_channel`."""
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

    async def purge_rule(self, rule_id: UUID) -> PurgeNotificationRulePayload:
        """Permanently remove a notification rule."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/rules/{rule_id}",
            response_model=PurgeNotificationRulePayload,
        )

    async def partial_bulk_update_rules(
        self, request: PartialBulkUpdateNotificationRulesInput
    ) -> PartialBulkPayload[NotificationRuleNode]:
        """Update several notification rules, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/rules/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[NotificationRuleNode],
        )

    async def partial_bulk_purge_rules(
        self, request: PartialBulkPurgeNotificationRulesInput
    ) -> PartialBulkPayload[NotificationRuleNode]:
        """Permanently remove several notification rules, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/rules/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPayload[NotificationRuleNode],
        )

    async def delete_rule(
        self, request: DeleteNotificationRuleInput
    ) -> DeleteNotificationRulePayload:
        """Deprecated. Use :meth:`purge_rule`."""
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
