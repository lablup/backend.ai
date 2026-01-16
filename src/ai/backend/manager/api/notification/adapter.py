"""
Adapters to convert notification DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.data.notification.types import (
    EmailSpec,
    NotificationChannelType,
    WebhookSpec,
)
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
    WebhookSpecResponse,
)
from ai.backend.common.dto.manager.notification.response import EmailSpecResponse
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.errors.notification import InvalidNotificationSpec
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationChannelOrders,
    NotificationRuleConditions,
    NotificationRuleOrders,
)
from ai.backend.manager.repositories.notification.updaters import (
    NotificationChannelUpdaterSpec,
    NotificationRuleUpdaterSpec,
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
        response: WebhookSpecResponse | EmailSpecResponse
        match data.channel_type:
            case NotificationChannelType.WEBHOOK:
                if not isinstance(data.spec, WebhookSpec):
                    raise InvalidNotificationSpec(
                        f"Expected WebhookSpec for WEBHOOK channel, got {type(data.spec).__name__}"
                    )
                response = WebhookSpecResponse(url=data.spec.url)
            case NotificationChannelType.EMAIL:
                if not isinstance(data.spec, EmailSpec):
                    raise InvalidNotificationSpec(
                        f"Expected EmailSpec for EMAIL channel, got {type(data.spec).__name__}"
                    )
                response = EmailSpecResponse(
                    smtp=data.spec.smtp,
                    message=data.spec.message,
                    auth=data.spec.auth,
                )
        return NotificationChannelDTO(
            id=data.id,
            name=data.name,
            description=data.description,
            channel_type=data.channel_type,
            spec=response,
            enabled=data.enabled,
            created_at=data.created_at,
            created_by=data.created_by,
            updated_at=data.updated_at,
        )

    def build_updater(
        self, request: UpdateNotificationChannelRequest, channel_id: UUID
    ) -> Updater[NotificationChannelRow]:
        """Convert update request to updater."""

        name = OptionalState[str].nop()
        description = OptionalState[str | None].nop()
        spec = OptionalState[WebhookSpec | EmailSpec].nop()
        enabled = OptionalState[bool].nop()

        if request.name is not None:
            name = OptionalState.update(request.name)
        if request.description is not None:
            description = OptionalState.update(request.description)
        if request.spec is not None:
            # spec validator ensures this is WebhookSpec or EmailSpec
            if not isinstance(request.spec, WebhookSpec | EmailSpec):
                raise InvalidNotificationSpec(
                    f"Expected WebhookSpec or EmailSpec, got {type(request.spec).__name__}"
                )
            spec = OptionalState.update(request.spec)
        if request.enabled is not None:
            enabled = OptionalState.update(request.enabled)

        updater_spec = NotificationChannelUpdaterSpec(
            name=name,
            description=description,
            spec=spec,
            enabled=enabled,
        )
        return Updater(spec=updater_spec, pk_value=channel_id)

    def build_querier(self, request: SearchNotificationChannelsRequest) -> BatchQuerier:
        """
        Build a BatchQuerier for notification channels from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            BatchQuerier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: NotificationChannelFilter) -> list[QueryCondition]:
        """Convert channel filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Name filter
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=NotificationChannelConditions.by_name_contains,
                equals_factory=NotificationChannelConditions.by_name_equals,
                starts_with_factory=NotificationChannelConditions.by_name_starts_with,
                ends_with_factory=NotificationChannelConditions.by_name_ends_with,
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
        if order.field == NotificationChannelOrderField.CREATED_AT:
            return NotificationChannelOrders.created_at(ascending=ascending)
        if order.field == NotificationChannelOrderField.UPDATED_AT:
            return NotificationChannelOrders.updated_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


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

    def build_updater(
        self, request: UpdateNotificationRuleRequest, rule_id: UUID
    ) -> Updater[NotificationRuleRow]:
        """Convert update request to updater."""
        name = OptionalState[str].nop()
        description = OptionalState[str | None].nop()
        message_template = OptionalState[str].nop()
        enabled = OptionalState[bool].nop()

        if request.name is not None:
            name = OptionalState.update(request.name)
        if request.description is not None:
            description = OptionalState.update(request.description)
        if request.message_template is not None:
            message_template = OptionalState.update(request.message_template)
        if request.enabled is not None:
            enabled = OptionalState.update(request.enabled)

        spec = NotificationRuleUpdaterSpec(
            name=name,
            description=description,
            message_template=message_template,
            enabled=enabled,
        )
        return Updater(spec=spec, pk_value=rule_id)

    def build_querier(self, request: SearchNotificationRulesRequest) -> BatchQuerier:
        """
        Build a BatchQuerier for notification rules from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            BatchQuerier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: NotificationRuleFilter) -> list[QueryCondition]:
        """Convert rule filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Name filter
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=NotificationRuleConditions.by_name_contains,
                equals_factory=NotificationRuleConditions.by_name_equals,
                starts_with_factory=NotificationRuleConditions.by_name_starts_with,
                ends_with_factory=NotificationRuleConditions.by_name_ends_with,
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
        if order.field == NotificationRuleOrderField.CREATED_AT:
            return NotificationRuleOrders.created_at(ascending=ascending)
        if order.field == NotificationRuleOrderField.UPDATED_AT:
            return NotificationRuleOrders.updated_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
