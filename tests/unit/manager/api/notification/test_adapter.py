"""
Tests for notification API adapter classes.
Tests conversion from DTO objects to repository Querier objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import uuid4

from ai.backend.common.data.notification import NotificationChannelType, NotificationRuleType
from ai.backend.common.data.notification import WebhookConfig as WebhookConfigData
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
    StringFilter,
    UpdateNotificationChannelRequest,
    UpdateNotificationRuleRequest,
    WebhookConfigResponse,
)
from ai.backend.common.dto.manager.notification.request import (
    SearchNotificationChannelsRequest,
    SearchNotificationRulesRequest,
)
from ai.backend.manager.api.notification.adapter import (
    NotificationChannelAdapter,
    NotificationRuleAdapter,
)
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.repositories.base import OffsetPagination
from ai.backend.manager.repositories.notification.updaters import (
    NotificationChannelUpdaterSpec,
    NotificationRuleUpdaterSpec,
)


class TestNotificationChannelAdapter:
    """Test cases for NotificationChannelAdapter"""

    def test_empty_querier(self) -> None:
        """Test building querier with no filters, orders, and default limit"""
        request = SearchNotificationChannelsRequest()
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 0
        assert len(querier.orders) == 0
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 50
        assert querier.pagination.offset == 0

    def test_name_equals_case_sensitive(self) -> None:
        """Test name equals filter (case-sensitive)"""
        request = SearchNotificationChannelsRequest(
            filter=NotificationChannelFilter(
                name=StringFilter(equals="Test Channel"),
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        # Verify condition is callable and returns ColumnElement
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_equals_case_insensitive(self) -> None:
        """Test name equals filter (case-insensitive)"""
        request = SearchNotificationChannelsRequest(
            filter=NotificationChannelFilter(
                name=StringFilter(i_equals="test channel"),
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_contains_case_sensitive(self) -> None:
        """Test name contains filter (case-sensitive)"""
        request = SearchNotificationChannelsRequest(
            filter=NotificationChannelFilter(
                name=StringFilter(contains="Test"),
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_contains_case_insensitive(self) -> None:
        """Test name contains filter (case-insensitive)"""
        request = SearchNotificationChannelsRequest(
            filter=NotificationChannelFilter(
                name=StringFilter(i_contains="test"),
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_channel_types_filter(self) -> None:
        """Test channel types filter"""
        request = SearchNotificationChannelsRequest(
            filter=NotificationChannelFilter(
                channel_types=[NotificationChannelType.WEBHOOK],
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_enabled_filter_true(self) -> None:
        """Test enabled filter (True)"""
        request = SearchNotificationChannelsRequest(filter=NotificationChannelFilter(enabled=True))
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_enabled_filter_false(self) -> None:
        """Test enabled filter (False)"""
        request = SearchNotificationChannelsRequest(filter=NotificationChannelFilter(enabled=False))
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_multiple_filters_combined(self) -> None:
        """Test multiple filters combined"""
        request = SearchNotificationChannelsRequest(
            filter=NotificationChannelFilter(
                name=StringFilter(contains="Test"),
                channel_types=[NotificationChannelType.WEBHOOK],
                enabled=True,
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        # Should have 3 conditions
        assert len(querier.conditions) == 3
        for condition in querier.conditions:
            assert condition() is not None

    def test_order_by_name_ascending(self) -> None:
        """Test ordering by name ascending"""
        request = SearchNotificationChannelsRequest(
            order=NotificationChannelOrder(
                field=NotificationChannelOrderField.NAME,
                direction=OrderDirection.ASC,
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_name_descending(self) -> None:
        """Test ordering by name descending"""
        request = SearchNotificationChannelsRequest(
            order=NotificationChannelOrder(
                field=NotificationChannelOrderField.NAME,
                direction=OrderDirection.DESC,
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_ascending(self) -> None:
        """Test ordering by created_at ascending"""
        request = SearchNotificationChannelsRequest(
            order=NotificationChannelOrder(
                field=NotificationChannelOrderField.CREATED_AT,
                direction=OrderDirection.ASC,
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_descending(self) -> None:
        """Test ordering by created_at descending"""
        request = SearchNotificationChannelsRequest(
            order=NotificationChannelOrder(
                field=NotificationChannelOrderField.CREATED_AT,
                direction=OrderDirection.DESC,
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_updated_at_ascending(self) -> None:
        """Test ordering by updated_at ascending"""
        request = SearchNotificationChannelsRequest(
            order=NotificationChannelOrder(
                field=NotificationChannelOrderField.UPDATED_AT,
                direction=OrderDirection.ASC,
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_updated_at_descending(self) -> None:
        """Test ordering by updated_at descending"""
        request = SearchNotificationChannelsRequest(
            order=NotificationChannelOrder(
                field=NotificationChannelOrderField.UPDATED_AT,
                direction=OrderDirection.DESC,
            )
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_pagination(self) -> None:
        """Test pagination parameters"""
        request = SearchNotificationChannelsRequest(limit=10, offset=5)
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5

    def test_filter_order_pagination_combined(self) -> None:
        """Test filter, order, and pagination all combined"""
        request = SearchNotificationChannelsRequest(
            filter=NotificationChannelFilter(
                name=StringFilter(contains="Test"),
                enabled=True,
            ),
            order=NotificationChannelOrder(
                field=NotificationChannelOrderField.NAME,
                direction=OrderDirection.ASC,
            ),
            limit=20,
            offset=10,
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 2
        assert len(querier.orders) == 1
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10


class TestNotificationRuleAdapter:
    """Test cases for NotificationRuleAdapter"""

    def test_empty_querier(self) -> None:
        """Test building querier with no filters, orders, and default limit"""
        request = SearchNotificationRulesRequest()
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 0
        assert len(querier.orders) == 0
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 50
        assert querier.pagination.offset == 0

    def test_name_equals_case_sensitive(self) -> None:
        """Test name equals filter (case-sensitive)"""
        request = SearchNotificationRulesRequest(
            filter=NotificationRuleFilter(
                name=StringFilter(equals="Test Rule"),
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_equals_case_insensitive(self) -> None:
        """Test name equals filter (case-insensitive)"""
        request = SearchNotificationRulesRequest(
            filter=NotificationRuleFilter(
                name=StringFilter(i_equals="test rule"),
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_contains_case_sensitive(self) -> None:
        """Test name contains filter (case-sensitive)"""
        request = SearchNotificationRulesRequest(
            filter=NotificationRuleFilter(
                name=StringFilter(contains="Test"),
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_contains_case_insensitive(self) -> None:
        """Test name contains filter (case-insensitive)"""
        request = SearchNotificationRulesRequest(
            filter=NotificationRuleFilter(
                name=StringFilter(i_contains="test"),
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_rule_types_filter(self) -> None:
        """Test rule types filter"""
        request = SearchNotificationRulesRequest(
            filter=NotificationRuleFilter(
                rule_types=[NotificationRuleType.SESSION_STARTED],
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_enabled_filter_true(self) -> None:
        """Test enabled filter (True)"""
        request = SearchNotificationRulesRequest(filter=NotificationRuleFilter(enabled=True))
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_enabled_filter_false(self) -> None:
        """Test enabled filter (False)"""
        request = SearchNotificationRulesRequest(filter=NotificationRuleFilter(enabled=False))
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_multiple_filters_combined(self) -> None:
        """Test multiple filters combined"""
        request = SearchNotificationRulesRequest(
            filter=NotificationRuleFilter(
                name=StringFilter(contains="Test"),
                rule_types=[NotificationRuleType.SESSION_STARTED],
                enabled=True,
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        # Should have 3 conditions
        assert len(querier.conditions) == 3
        for condition in querier.conditions:
            assert condition() is not None

    def test_order_by_name_ascending(self) -> None:
        """Test ordering by name ascending"""
        request = SearchNotificationRulesRequest(
            order=NotificationRuleOrder(
                field=NotificationRuleOrderField.NAME,
                direction=OrderDirection.ASC,
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_name_descending(self) -> None:
        """Test ordering by name descending"""
        request = SearchNotificationRulesRequest(
            order=NotificationRuleOrder(
                field=NotificationRuleOrderField.NAME,
                direction=OrderDirection.DESC,
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_ascending(self) -> None:
        """Test ordering by created_at ascending"""
        request = SearchNotificationRulesRequest(
            order=NotificationRuleOrder(
                field=NotificationRuleOrderField.CREATED_AT,
                direction=OrderDirection.ASC,
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_descending(self) -> None:
        """Test ordering by created_at descending"""
        request = SearchNotificationRulesRequest(
            order=NotificationRuleOrder(
                field=NotificationRuleOrderField.CREATED_AT,
                direction=OrderDirection.DESC,
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_updated_at_ascending(self) -> None:
        """Test ordering by updated_at ascending"""
        request = SearchNotificationRulesRequest(
            order=NotificationRuleOrder(
                field=NotificationRuleOrderField.UPDATED_AT,
                direction=OrderDirection.ASC,
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_updated_at_descending(self) -> None:
        """Test ordering by updated_at descending"""
        request = SearchNotificationRulesRequest(
            order=NotificationRuleOrder(
                field=NotificationRuleOrderField.UPDATED_AT,
                direction=OrderDirection.DESC,
            )
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_pagination(self) -> None:
        """Test pagination parameters"""
        request = SearchNotificationRulesRequest(limit=10, offset=5)
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5

    def test_filter_order_pagination_combined(self) -> None:
        """Test filter, order, and pagination all combined"""
        request = SearchNotificationRulesRequest(
            filter=NotificationRuleFilter(
                name=StringFilter(contains="Test"),
                enabled=True,
            ),
            order=NotificationRuleOrder(
                field=NotificationRuleOrderField.NAME,
                direction=OrderDirection.ASC,
            ),
            limit=20,
            offset=10,
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 2
        assert len(querier.orders) == 1
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10


class TestNotificationChannelAdapterConversion:
    """Test cases for NotificationChannelAdapter data conversion methods"""

    def test_convert_to_dto(self) -> None:
        """Test converting NotificationChannelData to NotificationChannelDTO"""
        now = datetime.now()
        channel_id = uuid4()
        user_id = uuid4()

        channel_data = NotificationChannelData(
            id=channel_id,
            name="Test Channel",
            description="Test description",
            channel_type=NotificationChannelType.WEBHOOK,
            config=WebhookConfigData(url="https://example.com/webhook"),
            enabled=True,
            created_by=user_id,
            created_at=now,
            updated_at=now,
        )

        adapter = NotificationChannelAdapter()
        dto = adapter.convert_to_dto(channel_data)

        assert isinstance(dto, NotificationChannelDTO)
        assert dto.id == channel_id
        assert dto.name == "Test Channel"
        assert dto.description == "Test description"
        assert dto.channel_type == NotificationChannelType.WEBHOOK
        assert isinstance(dto.config, WebhookConfigResponse)
        assert dto.config.url == "https://example.com/webhook"
        assert dto.enabled is True
        assert dto.created_by == user_id
        assert dto.created_at == now
        assert dto.updated_at == now

    def test_build_updater_with_all_fields(self) -> None:
        """Test building updater with all fields updated"""
        channel_id = uuid4()
        request = UpdateNotificationChannelRequest(
            name="Updated Name",
            description="Updated description",
            config=WebhookConfigData(url="https://new-url.com"),
            enabled=False,
        )

        adapter = NotificationChannelAdapter()
        updater = adapter.build_updater(request, channel_id)
        spec = cast(NotificationChannelUpdaterSpec, updater.spec)

        assert spec.name.value() == "Updated Name"
        assert spec.description.value() == "Updated description"
        assert spec.config.value().url == "https://new-url.com"
        assert spec.enabled.value() is False
        assert updater.pk_value == channel_id

    def test_build_updater_with_partial_fields(self) -> None:
        """Test building updater with only some fields updated"""
        channel_id = uuid4()
        request = UpdateNotificationChannelRequest(
            name="Updated Name",
            enabled=False,
        )

        adapter = NotificationChannelAdapter()
        updater = adapter.build_updater(request, channel_id)
        spec = cast(NotificationChannelUpdaterSpec, updater.spec)

        assert spec.name.value() == "Updated Name"
        assert spec.description.optional_value() is None
        assert spec.config.optional_value() is None
        assert spec.enabled.value() is False
        assert updater.pk_value == channel_id


class TestNotificationRuleAdapterConversion:
    """Test cases for NotificationRuleAdapter data conversion methods"""

    def test_convert_to_dto(self) -> None:
        """Test converting NotificationRuleData to NotificationRuleDTO"""
        now = datetime.now()
        rule_id = uuid4()
        channel_id = uuid4()
        user_id = uuid4()

        channel_data = NotificationChannelData(
            id=channel_id,
            name="Test Channel",
            description="Channel description",
            channel_type=NotificationChannelType.WEBHOOK,
            config=WebhookConfigData(url="https://example.com/webhook"),
            enabled=True,
            created_by=user_id,
            created_at=now,
            updated_at=now,
        )

        rule_data = NotificationRuleData(
            id=rule_id,
            name="Test Rule",
            description="Rule description",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=channel_data,
            message_template="Session {{ session_id }} started",
            enabled=True,
            created_by=user_id,
            created_at=now,
            updated_at=now,
        )

        adapter = NotificationRuleAdapter()
        dto = adapter.convert_to_dto(rule_data)

        assert isinstance(dto, NotificationRuleDTO)
        assert dto.id == rule_id
        assert dto.name == "Test Rule"
        assert dto.description == "Rule description"
        assert dto.rule_type == NotificationRuleType.SESSION_STARTED
        assert isinstance(dto.channel, NotificationChannelDTO)
        assert dto.channel.id == channel_id
        assert dto.channel.name == "Test Channel"
        assert dto.message_template == "Session {{ session_id }} started"
        assert dto.enabled is True
        assert dto.created_by == user_id
        assert dto.created_at == now
        assert dto.updated_at == now

    def test_build_updater_with_all_fields(self) -> None:
        """Test building updater with all fields updated"""
        rule_id = uuid4()
        request = UpdateNotificationRuleRequest(
            name="Updated Rule",
            description="Updated description",
            message_template="New template {{ data }}",
            enabled=False,
        )

        adapter = NotificationRuleAdapter()
        updater = adapter.build_updater(request, rule_id)
        spec = cast(NotificationRuleUpdaterSpec, updater.spec)

        assert spec.name.value() == "Updated Rule"
        assert spec.description.value() == "Updated description"
        assert spec.message_template.value() == "New template {{ data }}"
        assert spec.enabled.value() is False
        assert updater.pk_value == rule_id

    def test_build_updater_with_partial_fields(self) -> None:
        """Test building updater with only some fields updated"""
        rule_id = uuid4()
        request = UpdateNotificationRuleRequest(
            name="Updated Rule",
            enabled=False,
        )

        adapter = NotificationRuleAdapter()
        updater = adapter.build_updater(request, rule_id)
        spec = cast(NotificationRuleUpdaterSpec, updater.spec)

        assert spec.name.value() == "Updated Rule"
        assert spec.description.optional_value() is None
        assert spec.message_template.optional_value() is None
        assert spec.enabled.value() is False
        assert updater.pk_value == rule_id
