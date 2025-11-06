"""
Adapters to convert notification DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from typing import Optional

from ai.backend.common.dto.manager.notification import (
    NotificationChannelDTO,
    NotificationChannelFilter,
    NotificationChannelOrder,
    NotificationChannelOrderField,
    NotificationRuleDTO,
    NotificationRuleFilter,
    NotificationRuleOrder,
    NotificationRuleOrderField,
    OrderDirection,
    SearchNotificationChannelsRequest,
    SearchNotificationRulesRequest,
    UpdateNotificationChannelRequest,
    UpdateNotificationRuleRequest,
    WebhookConfigResponse,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationChannelModifier,
    NotificationRuleData,
    NotificationRuleModifier,
)
from ai.backend.manager.repositories.base import (
    OffsetPagination,
    Querier,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationChannelOrders,
    NotificationRuleConditions,
    NotificationRuleOrders,
)
from ai.backend.manager.types import OptionalState

__all__ = (
    "NotificationChannelAdapter",
    "NotificationRuleAdapter",
)


class NotificationChannelAdapter(BaseFilterAdapter):
    """Adapter for converting notification channel requests to repository queries."""

    def convert_to_dto(self, data: NotificationChannelData) -> NotificationChannelDTO:
        """Convert NotificationChannelData to DTO."""
        return NotificationChannelDTO(
            id=data.id,
            name=data.name,
            description=data.description,
            channel_type=data.channel_type,
            config=WebhookConfigResponse(url=data.config.url),
            enabled=data.enabled,
            created_at=data.created_at,
            created_by=data.created_by,
            updated_at=data.updated_at,
        )

    def build_modifier(
        self, request: UpdateNotificationChannelRequest
    ) -> NotificationChannelModifier:
        """Convert update request to modifier."""
        from ai.backend.common.data.notification import WebhookConfig

        modifier = NotificationChannelModifier()
        if request.name is not None:
            modifier.name = OptionalState.update(request.name)
        if request.description is not None:
            modifier.description = OptionalState.update(request.description)
        if request.config is not None:
            # config validator ensures this is WebhookConfig
            assert isinstance(request.config, WebhookConfig)
            modifier.config = OptionalState.update(request.config)
        if request.enabled is not None:
            modifier.enabled = OptionalState.update(request.enabled)
        return modifier

    def build_querier(self, request: SearchNotificationChannelsRequest) -> Querier:
        """
        Build a Querier for notification channels from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            Querier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(request.order)] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return Querier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: NotificationChannelFilter) -> list[QueryCondition]:
        """Convert channel filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Name filter
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                equals_fn=NotificationChannelConditions.by_name_equals,
                contains_fn=NotificationChannelConditions.by_name_contains,
            )
            if condition is not None:
                conditions.append(condition)

        # Channel types filter
        if filter.channel_types is not None and len(filter.channel_types) > 0:
            conditions.append(NotificationChannelConditions.by_channel_types(filter.channel_types))

        # Enabled filter
        if filter.enabled is not None:
            conditions.append(NotificationChannelConditions.by_enabled(filter.enabled))

        return conditions

    def _convert_order(self, order: NotificationChannelOrder) -> QueryOrder:
        """Convert channel order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == NotificationChannelOrderField.NAME:
            return NotificationChannelOrders.name(ascending=ascending)
        elif order.field == NotificationChannelOrderField.CREATED_AT:
            return NotificationChannelOrders.created_at(ascending=ascending)
        elif order.field == NotificationChannelOrderField.UPDATED_AT:
            return NotificationChannelOrders.updated_at(ascending=ascending)
        else:
            raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(
        self, limit: Optional[int], offset: Optional[int]
    ) -> Optional[OffsetPagination]:
        """Build pagination from limit and offset."""
        if limit is None:
            return None
        return OffsetPagination(limit=limit, offset=offset or 0)


class NotificationRuleAdapter(BaseFilterAdapter):
    """Adapter for converting notification rule requests to repository queries."""

    def convert_to_dto(self, data: NotificationRuleData) -> NotificationRuleDTO:
        """Convert NotificationRuleData to DTO."""
        channel_adapter = NotificationChannelAdapter()
        return NotificationRuleDTO(
            id=data.id,
            name=data.name,
            description=data.description,
            rule_type=data.rule_type,
            channel=channel_adapter.convert_to_dto(data.channel),
            message_template=data.message_template,
            enabled=data.enabled,
            created_at=data.created_at,
            created_by=data.created_by,
            updated_at=data.updated_at,
        )

    def build_modifier(self, request: UpdateNotificationRuleRequest) -> NotificationRuleModifier:
        """Convert update request to modifier."""
        modifier = NotificationRuleModifier()
        if request.name is not None:
            modifier.name = OptionalState.update(request.name)
        if request.description is not None:
            modifier.description = OptionalState.update(request.description)
        if request.message_template is not None:
            modifier.message_template = OptionalState.update(request.message_template)
        if request.enabled is not None:
            modifier.enabled = OptionalState.update(request.enabled)
        return modifier

    def build_querier(self, request: SearchNotificationRulesRequest) -> Querier:
        """
        Build a Querier for notification rules from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            Querier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(request.order)] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return Querier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: NotificationRuleFilter) -> list[QueryCondition]:
        """Convert rule filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Name filter
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                equals_fn=NotificationRuleConditions.by_name_equals,
                contains_fn=NotificationRuleConditions.by_name_contains,
            )
            if condition is not None:
                conditions.append(condition)

        # Rule types filter
        if filter.rule_types is not None and len(filter.rule_types) > 0:
            conditions.append(NotificationRuleConditions.by_rule_types(filter.rule_types))

        # Enabled filter
        if filter.enabled is not None:
            conditions.append(NotificationRuleConditions.by_enabled(filter.enabled))

        return conditions

    def _convert_order(self, order: NotificationRuleOrder) -> QueryOrder:
        """Convert rule order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == NotificationRuleOrderField.NAME:
            return NotificationRuleOrders.name(ascending=ascending)
        elif order.field == NotificationRuleOrderField.CREATED_AT:
            return NotificationRuleOrders.created_at(ascending=ascending)
        elif order.field == NotificationRuleOrderField.UPDATED_AT:
            return NotificationRuleOrders.updated_at(ascending=ascending)
        else:
            raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(
        self, limit: Optional[int], offset: Optional[int]
    ) -> Optional[OffsetPagination]:
        """Build pagination from limit and offset."""
        if limit is None:
            return None
        return OffsetPagination(limit=limit, offset=offset or 0)
