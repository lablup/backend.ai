from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.data.notification.types import NotificationRuleType
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
    NotificationRuleTypeSchemaResponse,
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


class NotificationClient(BaseDomainClient):
    """SDK v2 client for notification channel and rule management endpoints."""

    # ---- Channels ----

    async def create_channel(
        self, request: CreateNotificationChannelRequest
    ) -> CreateNotificationChannelResponse:
        return await self._client.typed_request(
            "POST",
            "/notifications/channels",
            request=request,
            response_model=CreateNotificationChannelResponse,
        )

    async def search_channels(
        self, request: SearchNotificationChannelsRequest
    ) -> ListNotificationChannelsResponse:
        return await self._client.typed_request(
            "POST",
            "/notifications/channels/search",
            request=request,
            response_model=ListNotificationChannelsResponse,
        )

    async def get_channel(self, channel_id: uuid.UUID) -> GetNotificationChannelResponse:
        return await self._client.typed_request(
            "GET",
            f"/notifications/channels/{channel_id}",
            response_model=GetNotificationChannelResponse,
        )

    async def update_channel(
        self, channel_id: uuid.UUID, request: UpdateNotificationChannelRequest
    ) -> UpdateNotificationChannelResponse:
        return await self._client.typed_request(
            "PATCH",
            f"/notifications/channels/{channel_id}",
            request=request,
            response_model=UpdateNotificationChannelResponse,
        )

    async def delete_channel(self, channel_id: uuid.UUID) -> DeleteNotificationChannelResponse:
        return await self._client.typed_request(
            "DELETE",
            f"/notifications/channels/{channel_id}",
            response_model=DeleteNotificationChannelResponse,
        )

    async def validate_channel(
        self, channel_id: uuid.UUID, request: ValidateNotificationChannelRequest
    ) -> ValidateNotificationChannelResponse:
        return await self._client.typed_request(
            "POST",
            f"/notifications/channels/{channel_id}/validate",
            request=request,
            response_model=ValidateNotificationChannelResponse,
        )

    # ---- Rules ----

    async def list_rule_types(self) -> ListNotificationRuleTypesResponse:
        return await self._client.typed_request(
            "GET",
            "/notifications/rule-types",
            response_model=ListNotificationRuleTypesResponse,
        )

    async def get_rule_type_schema(
        self, rule_type: NotificationRuleType
    ) -> NotificationRuleTypeSchemaResponse:
        return await self._client.typed_request(
            "GET",
            f"/notifications/rule-types/{rule_type}/schema",
            response_model=NotificationRuleTypeSchemaResponse,
        )

    async def create_rule(
        self, request: CreateNotificationRuleRequest
    ) -> CreateNotificationRuleResponse:
        return await self._client.typed_request(
            "POST",
            "/notifications/rules",
            request=request,
            response_model=CreateNotificationRuleResponse,
        )

    async def search_rules(
        self, request: SearchNotificationRulesRequest
    ) -> ListNotificationRulesResponse:
        return await self._client.typed_request(
            "POST",
            "/notifications/rules/search",
            request=request,
            response_model=ListNotificationRulesResponse,
        )

    async def get_rule(self, rule_id: uuid.UUID) -> GetNotificationRuleResponse:
        return await self._client.typed_request(
            "GET",
            f"/notifications/rules/{rule_id}",
            response_model=GetNotificationRuleResponse,
        )

    async def update_rule(
        self, rule_id: uuid.UUID, request: UpdateNotificationRuleRequest
    ) -> UpdateNotificationRuleResponse:
        return await self._client.typed_request(
            "PATCH",
            f"/notifications/rules/{rule_id}",
            request=request,
            response_model=UpdateNotificationRuleResponse,
        )

    async def delete_rule(self, rule_id: uuid.UUID) -> DeleteNotificationRuleResponse:
        return await self._client.typed_request(
            "DELETE",
            f"/notifications/rules/{rule_id}",
            response_model=DeleteNotificationRuleResponse,
        )

    async def validate_rule(
        self, rule_id: uuid.UUID, request: ValidateNotificationRuleRequest
    ) -> ValidateNotificationRuleResponse:
        return await self._client.typed_request(
            "POST",
            f"/notifications/rules/{rule_id}/validate",
            request=request,
            response_model=ValidateNotificationRuleResponse,
        )
