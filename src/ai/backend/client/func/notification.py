"""Client SDK functions for notification system."""

from __future__ import annotations

from uuid import UUID

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

from ..request import Request
from .base import BaseFunction, api_function

__all__ = ("Notification",)


class Notification(BaseFunction):
    """
    Provides functions to interact with the notification system.
    Supports both notification channels and rules.
    """

    # Channel CRUD operations

    @api_function
    @classmethod
    async def create_channel(
        cls,
        request: CreateNotificationChannelRequest,
    ) -> CreateNotificationChannelResponse:
        """
        Create a new notification channel.

        :param request: Channel creation request
        :returns: The created channel data
        """
        rqst = Request("POST", "/notifications/channels")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return CreateNotificationChannelResponse.model_validate(data)

    @api_function
    @classmethod
    async def list_channels(
        cls,
        request: SearchNotificationChannelsRequest,
    ) -> ListNotificationChannelsResponse:
        """
        List all notification channels.

        :param request: Channel listing request
        :returns: List of channels
        """
        rqst = Request("POST", "/notifications/channels/search")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListNotificationChannelsResponse.model_validate(data)

    @api_function
    @classmethod
    async def get_channel(
        cls,
        channel_id: UUID,
    ) -> GetNotificationChannelResponse:
        """
        Get a notification channel by ID.

        :param channel_id: Channel ID
        :returns: The channel data
        """
        rqst = Request("GET", f"/notifications/channels/{channel_id}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetNotificationChannelResponse.model_validate(data)

    @api_function
    @classmethod
    async def update_channel(
        cls,
        channel_id: UUID,
        request: UpdateNotificationChannelRequest,
    ) -> UpdateNotificationChannelResponse:
        """
        Update a notification channel.

        :param channel_id: Channel ID to update
        :param request: Channel update request
        :returns: The updated channel data
        """
        rqst = Request("PATCH", f"/notifications/channels/{channel_id}")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return UpdateNotificationChannelResponse.model_validate(data)

    @api_function
    @classmethod
    async def delete_channel(
        cls,
        channel_id: UUID,
    ) -> DeleteNotificationChannelResponse:
        """
        Delete a notification channel.

        :param channel_id: Channel ID to delete
        :returns: Deletion confirmation
        """
        rqst = Request("DELETE", f"/notifications/channels/{channel_id}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return DeleteNotificationChannelResponse.model_validate(data)

    @api_function
    @classmethod
    async def validate_channel(
        cls,
        channel_id: UUID,
        request: ValidateNotificationChannelRequest,
    ) -> ValidateNotificationChannelResponse:
        """
        Validate a notification channel by sending a test webhook.

        :param channel_id: Channel ID to validate
        :param request: Validation request with test message
        :returns: Validation result
        """
        rqst = Request("POST", f"/notifications/channels/{channel_id}/validate")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ValidateNotificationChannelResponse.model_validate(data)

    # Rule CRUD operations

    @api_function
    @classmethod
    async def create_rule(
        cls,
        request: CreateNotificationRuleRequest,
    ) -> CreateNotificationRuleResponse:
        """
        Create a new notification rule.

        :param request: Rule creation request
        :returns: The created rule data
        """
        rqst = Request("POST", "/notifications/rules")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return CreateNotificationRuleResponse.model_validate(data)

    @api_function
    @classmethod
    async def list_rules(
        cls,
        request: SearchNotificationRulesRequest,
    ) -> ListNotificationRulesResponse:
        """
        List all notification rules.

        :param request: Rule listing request
        :returns: List of rules
        """
        rqst = Request("POST", "/notifications/rules/search")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListNotificationRulesResponse.model_validate(data)

    @api_function
    @classmethod
    async def get_rule(
        cls,
        rule_id: UUID,
    ) -> GetNotificationRuleResponse:
        """
        Get a notification rule by ID.

        :param rule_id: Rule ID
        :returns: The rule data
        """
        rqst = Request("GET", f"/notifications/rules/{rule_id}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetNotificationRuleResponse.model_validate(data)

    @api_function
    @classmethod
    async def update_rule(
        cls,
        rule_id: UUID,
        request: UpdateNotificationRuleRequest,
    ) -> UpdateNotificationRuleResponse:
        """
        Update a notification rule.

        :param rule_id: Rule ID to update
        :param request: Rule update request
        :returns: The updated rule data
        """
        rqst = Request("PATCH", f"/notifications/rules/{rule_id}")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return UpdateNotificationRuleResponse.model_validate(data)

    @api_function
    @classmethod
    async def delete_rule(
        cls,
        rule_id: UUID,
    ) -> DeleteNotificationRuleResponse:
        """
        Delete a notification rule.

        :param rule_id: Rule ID to delete
        :returns: Deletion confirmation
        """
        rqst = Request("DELETE", f"/notifications/rules/{rule_id}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return DeleteNotificationRuleResponse.model_validate(data)

    @api_function
    @classmethod
    async def validate_rule(
        cls,
        rule_id: UUID,
        request: ValidateNotificationRuleRequest,
    ) -> ValidateNotificationRuleResponse:
        """
        Validate a notification rule by rendering its template with test data.

        :param rule_id: Rule ID to validate
        :param request: Validation request containing test notification data
        :returns: Validation result with rendered message
        """
        rqst = Request("POST", f"/notifications/rules/{rule_id}/validate")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ValidateNotificationRuleResponse.model_validate(data)

    @api_function
    @classmethod
    async def list_rule_types(cls) -> ListNotificationRuleTypesResponse:
        """
        List all available notification rule types.

        :returns: List of available rule types
        """
        rqst = Request("GET", "/notifications/rule-types")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListNotificationRuleTypesResponse.model_validate(data)

    @api_function
    @classmethod
    async def get_rule_type_schema(
        cls, rule_type: NotificationRuleType
    ) -> NotificationRuleTypeSchemaResponse:
        """
        Get JSON schema for a notification rule type's message format.

        :param rule_type: The notification rule type
        :returns: Schema information for the rule type
        """
        rqst = Request("GET", f"/notifications/rule-types/{rule_type.value}/schema")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return NotificationRuleTypeSchemaResponse.model_validate(data)
