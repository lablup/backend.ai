"""
Tests for AutoScalingService search functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource
from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleData,
    EndpointAutoScalingRuleListResult,
    RequesterCtx,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.model_serving.actions.search_auto_scaling_rules import (
    SearchAutoScalingRulesAction,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService


class TestAutoScalingServiceSearch:
    """Test cases for AutoScalingService search functionality"""

    @pytest.fixture
    def sample_auto_scaling_rule_data(self) -> EndpointAutoScalingRuleData:
        """Create sample auto scaling rule data"""
        return EndpointAutoScalingRuleData(
            id=uuid.uuid4(),
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu_util",
            threshold="80.0",
            comparator=AutoScalingMetricComparator.GREATER_THAN,
            step_size=1,
            cooldown_seconds=300,
            min_replicas=1,
            max_replicas=10,
            created_at=datetime.now(timezone.utc),
            last_triggered_at=datetime.now(timezone.utc),
            endpoint=uuid.uuid4(),
        )

    @pytest.fixture
    def sample_requester_ctx(self) -> RequesterCtx:
        """Create sample requester context"""
        return RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.USER,
            domain_name="default",
        )

    async def test_search_auto_scaling_rules(
        self,
        auto_scaling_service: AutoScalingService,
        mock_repositories: MagicMock,
        sample_auto_scaling_rule_data: EndpointAutoScalingRuleData,
        sample_requester_ctx: RequesterCtx,
    ) -> None:
        """Test searching auto scaling rules with querier"""
        mock_repositories.repository.search_auto_scaling_rules_validated = AsyncMock(
            return_value=EndpointAutoScalingRuleListResult(
                items=[sample_auto_scaling_rule_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchAutoScalingRulesAction(
            querier=querier,
            requester_ctx=sample_requester_ctx,
        )
        result = await auto_scaling_service.search_auto_scaling_rules(action)

        assert result.rules == [sample_auto_scaling_rule_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False

    async def test_search_auto_scaling_rules_empty_result(
        self,
        auto_scaling_service: AutoScalingService,
        mock_repositories: MagicMock,
        sample_requester_ctx: RequesterCtx,
    ) -> None:
        """Test searching auto scaling rules when no results are found"""
        mock_repositories.repository.search_auto_scaling_rules_validated = AsyncMock(
            return_value=EndpointAutoScalingRuleListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchAutoScalingRulesAction(
            querier=querier,
            requester_ctx=sample_requester_ctx,
        )
        result = await auto_scaling_service.search_auto_scaling_rules(action)

        assert result.rules == []
        assert result.total_count == 0

    async def test_search_auto_scaling_rules_with_pagination(
        self,
        auto_scaling_service: AutoScalingService,
        mock_repositories: MagicMock,
        sample_auto_scaling_rule_data: EndpointAutoScalingRuleData,
        sample_requester_ctx: RequesterCtx,
    ) -> None:
        """Test searching auto scaling rules with pagination"""
        mock_repositories.repository.search_auto_scaling_rules_validated = AsyncMock(
            return_value=EndpointAutoScalingRuleListResult(
                items=[sample_auto_scaling_rule_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchAutoScalingRulesAction(
            querier=querier,
            requester_ctx=sample_requester_ctx,
        )
        result = await auto_scaling_service.search_auto_scaling_rules(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
