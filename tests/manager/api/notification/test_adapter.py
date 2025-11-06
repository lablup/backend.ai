"""
Tests for notification API adapter classes.
Tests conversion from DTO objects to repository Querier objects.
"""

from __future__ import annotations

import pytest

from ai.backend.common.dto.manager.notification import (
    NotificationChannelFilter,
    NotificationChannelOrder,
    NotificationChannelOrderField,
    NotificationRuleFilter,
    NotificationRuleOrder,
    NotificationRuleOrderField,
    OrderDirection,
    StringFilter,
)
from ai.backend.common.data.notification import NotificationChannelType, NotificationRuleType
from ai.backend.manager.api.notification.adapter import (
    NotificationChannelAdapter,
    NotificationRuleAdapter,
)
from ai.backend.manager.dto.notification_request import (
    SearchNotificationChannelsReq,
    SearchNotificationRulesReq,
)


class TestNotificationChannelAdapter:
    """Test cases for NotificationChannelAdapter"""

    def test_empty_querier(self) -> None:
        """Test building querier with no filters, orders, or pagination"""
        request = SearchNotificationChannelsReq()
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 0
        assert len(querier.orders) == 0
        assert querier.pagination is None

    def test_name_equals_case_sensitive(self) -> None:
        """Test name equals filter (case-sensitive)"""
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
            filter=NotificationChannelFilter(enabled=True)
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_enabled_filter_false(self) -> None:
        """Test enabled filter (False)"""
        request = SearchNotificationChannelsReq(
            filter=NotificationChannelFilter(enabled=False)
        )
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_multiple_filters_combined(self) -> None:
        """Test multiple filters combined"""
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(
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
        request = SearchNotificationChannelsReq(limit=10, offset=5)
        adapter = NotificationChannelAdapter()
        querier = adapter.build_querier(request)

        assert querier.pagination is not None
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5

    def test_filter_order_pagination_combined(self) -> None:
        """Test filter, order, and pagination all combined"""
        request = SearchNotificationChannelsReq(
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
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10


class TestNotificationRuleAdapter:
    """Test cases for NotificationRuleAdapter"""

    def test_empty_querier(self) -> None:
        """Test building querier with no filters, orders, or pagination"""
        request = SearchNotificationRulesReq()
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 0
        assert len(querier.orders) == 0
        assert querier.pagination is None

    def test_name_equals_case_sensitive(self) -> None:
        """Test name equals filter (case-sensitive)"""
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
            filter=NotificationRuleFilter(enabled=True)
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_enabled_filter_false(self) -> None:
        """Test enabled filter (False)"""
        request = SearchNotificationRulesReq(
            filter=NotificationRuleFilter(enabled=False)
        )
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_multiple_filters_combined(self) -> None:
        """Test multiple filters combined"""
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(
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
        request = SearchNotificationRulesReq(limit=10, offset=5)
        adapter = NotificationRuleAdapter()
        querier = adapter.build_querier(request)

        assert querier.pagination is not None
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5

    def test_filter_order_pagination_combined(self) -> None:
        """Test filter, order, and pagination all combined"""
        request = SearchNotificationRulesReq(
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
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10
