"""
Tests for search_auto_scaling_rules_validated functionality.
Tests the repository layer for searching auto scaling rules with BatchQuerier.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleListResult,
)
from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination

if TYPE_CHECKING:
    from ai.backend.manager.repositories.model_serving.admin_repository import (
        AdminModelServingRepository,
    )
    from ai.backend.manager.repositories.model_serving.repository import (
        ModelServingRepository,
    )


class TestSearchAutoScalingRulesValidated:
    """Test cases for search_auto_scaling_rules_validated in ModelServingRepository."""

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture
    def sample_auto_scaling_rules(self, sample_endpoint) -> list[EndpointAutoScalingRuleRow]:
        """Create multiple sample auto scaling rules for testing."""
        rules = []
        metric_names = ["cpu_util", "memory_util", "gpu_util", "request_rate", "latency"]

        for i, metric_name in enumerate(metric_names):
            rule = EndpointAutoScalingRuleRow(
                id=uuid.uuid4(),
                endpoint=sample_endpoint.id,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name=metric_name,
                threshold=50.0 + i * 10,
                comparator=AutoScalingMetricComparator.GREATER_THAN,
                step_size=1 + i,
                cooldown_seconds=300 + i * 60,
                min_replicas=1,
                max_replicas=10 + i,
                created_at=datetime.now(timezone.utc),
                endpoint_row=sample_endpoint,
            )
            rules.append(rule)

        return rules

    @pytest.fixture
    def sample_rules_for_pagination(self, sample_endpoint) -> list[EndpointAutoScalingRuleRow]:
        """Create 25 sample auto scaling rules for pagination testing."""
        rules = []

        for i in range(25):
            rule = EndpointAutoScalingRuleRow(
                id=uuid.uuid4(),
                endpoint=sample_endpoint.id,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name=f"metric_{i:02d}",
                threshold=50.0 + i,
                comparator=AutoScalingMetricComparator.GREATER_THAN,
                step_size=1,
                cooldown_seconds=300,
                min_replicas=1,
                max_replicas=10,
                created_at=datetime.now(timezone.utc),
                endpoint_row=sample_endpoint,
            )
            rules.append(rule)

        return rules

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _create_mock_batch_result(
        self,
        rules: list[EndpointAutoScalingRuleRow],
        total_count: int | None = None,
        has_next_page: bool = False,
        has_previous_page: bool = False,
    ) -> MagicMock:
        """Create a mock result for execute_batch_querier."""
        mock_rows = []
        for rule in rules:
            mock_row = MagicMock()
            mock_row.EndpointAutoScalingRuleRow = rule
            mock_rows.append(mock_row)

        mock_result = MagicMock()
        mock_result.rows = mock_rows
        mock_result.total_count = total_count if total_count is not None else len(rules)
        mock_result.has_next_page = has_next_page
        mock_result.has_previous_page = has_previous_page

        return mock_result

    # =========================================================================
    # Tests - Basic Search
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_success(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_auto_scaling_rules: list[EndpointAutoScalingRuleRow],
        sample_user,
        mocker,
    ) -> None:
        """Test successful search of auto scaling rules with access validation."""
        # Arrange
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(sample_auto_scaling_rules)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert result is not None
        assert isinstance(result, EndpointAutoScalingRuleListResult)
        assert len(result.items) == len(sample_auto_scaling_rules)
        assert result.total_count == len(sample_auto_scaling_rules)
        mock_execute_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_empty_result(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_user,
        mocker,
    ) -> None:
        """Test search returns empty result when no rules match."""
        # Arrange
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result([], total_count=0)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert result is not None
        assert len(result.items) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_search_admin_access(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_auto_scaling_rules: list[EndpointAutoScalingRuleRow],
        sample_admin_user,
        mocker,
    ) -> None:
        """Test search with ADMIN role filters by domain."""
        # Arrange
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(sample_auto_scaling_rules)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_admin_user.uuid,
            user_role=UserRole.ADMIN,
            domain_name="default",
        )

        # Assert
        assert result is not None
        assert isinstance(result, EndpointAutoScalingRuleListResult)
        mock_execute_batch.assert_called_once()

    # =========================================================================
    # Tests - Pagination
    # =========================================================================

    @pytest.mark.asyncio
    async def test_pagination_first_page(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_rules_for_pagination: list[EndpointAutoScalingRuleRow],
        sample_user,
        mocker,
    ) -> None:
        """Test first page of offset-based pagination."""
        # Arrange
        first_page_rules = sample_rules_for_pagination[:10]
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(
            first_page_rules,
            total_count=25,
            has_next_page=True,
            has_previous_page=False,
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert len(result.items) == 10
        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is False

    @pytest.mark.asyncio
    async def test_pagination_second_page(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_rules_for_pagination: list[EndpointAutoScalingRuleRow],
        sample_user,
        mocker,
    ) -> None:
        """Test second page of offset-based pagination."""
        # Arrange
        second_page_rules = sample_rules_for_pagination[10:20]
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(
            second_page_rules,
            total_count=25,
            has_next_page=True,
            has_previous_page=True,
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert len(result.items) == 10
        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True

    @pytest.mark.asyncio
    async def test_pagination_last_page(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_rules_for_pagination: list[EndpointAutoScalingRuleRow],
        sample_user,
        mocker,
    ) -> None:
        """Test last page of offset-based pagination with partial results."""
        # Arrange
        last_page_rules = sample_rules_for_pagination[20:25]
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(
            last_page_rules,
            total_count=25,
            has_next_page=False,
            has_previous_page=True,
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert len(result.items) == 5
        assert result.total_count == 25
        assert result.has_next_page is False
        assert result.has_previous_page is True

    # =========================================================================
    # Tests - Filtering
    # =========================================================================

    @pytest.mark.asyncio
    async def test_filter_by_condition(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_auto_scaling_rules: list[EndpointAutoScalingRuleRow],
        sample_user,
        mocker,
    ) -> None:
        """Test search with filter condition."""
        # Arrange: Filter only rules with metric_name containing 'cpu'
        filtered_rules = [r for r in sample_auto_scaling_rules if "cpu" in r.metric_name]
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(filtered_rules)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: EndpointAutoScalingRuleRow.metric_name.contains("cpu"),
            ],
            orders=[],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert result is not None
        assert len(result.items) == len(filtered_rules)
        for item in result.items:
            assert "cpu" in item.metric_name

    # =========================================================================
    # Tests - Ordering
    # =========================================================================

    @pytest.mark.asyncio
    async def test_order_by_threshold_ascending(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_auto_scaling_rules: list[EndpointAutoScalingRuleRow],
        sample_user,
        mocker,
    ) -> None:
        """Test search with ascending order by threshold."""
        # Arrange: Sort rules by threshold ascending
        sorted_rules = sorted(sample_auto_scaling_rules, key=lambda r: float(r.threshold))
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(sorted_rules)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[EndpointAutoScalingRuleRow.threshold.asc()],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert result is not None
        thresholds = [float(item.threshold) for item in result.items]
        assert thresholds == sorted(thresholds)

    @pytest.mark.asyncio
    async def test_order_by_metric_name_descending(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_auto_scaling_rules: list[EndpointAutoScalingRuleRow],
        sample_user,
        mocker,
    ) -> None:
        """Test search with descending order by metric_name."""
        # Arrange: Sort rules by metric_name descending
        sorted_rules = sorted(sample_auto_scaling_rules, key=lambda r: r.metric_name, reverse=True)
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(sorted_rules)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[EndpointAutoScalingRuleRow.metric_name.desc()],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert result is not None
        metric_names = [item.metric_name for item in result.items]
        assert metric_names == sorted(metric_names, reverse=True)

    # =========================================================================
    # Tests - Combined Query (Pagination + Filter + Order)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_combined_pagination_filter_order(
        self,
        model_serving_repository: ModelServingRepository,
        setup_readonly_session,
        sample_auto_scaling_rules: list[EndpointAutoScalingRuleRow],
        sample_user,
        mocker,
    ) -> None:
        """Test search with pagination, filter, and ordering combined."""
        # Arrange: Filter rules with threshold > 60, sorted by threshold desc, limit 2
        filtered_sorted_rules = sorted(
            [r for r in sample_auto_scaling_rules if float(r.threshold) > 60],
            key=lambda r: float(r.threshold),
            reverse=True,
        )[:2]

        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(
            filtered_sorted_rules,
            total_count=3,
            has_next_page=True,
            has_previous_page=False,
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[
                lambda: EndpointAutoScalingRuleRow.threshold > 60,
            ],
            orders=[EndpointAutoScalingRuleRow.threshold.desc()],
        )

        # Act
        result = await model_serving_repository.search_auto_scaling_rules_validated(
            querier=querier,
            user_id=sample_user.uuid,
            user_role=UserRole.USER,
            domain_name="default",
        )

        # Assert
        assert result is not None
        assert len(result.items) == 2
        assert result.total_count == 3
        assert result.has_next_page is True

        # Verify ordering is descending
        thresholds = [float(item.threshold) for item in result.items]
        assert thresholds == sorted(thresholds, reverse=True)

        # Verify all returned items have threshold > 60
        for item in result.items:
            assert float(item.threshold) > 60


class TestSearchAutoScalingRulesForce:
    """Test cases for search_auto_scaling_rules_force in AdminModelServingRepository."""

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture
    def sample_auto_scaling_rules(self, sample_endpoint) -> list[EndpointAutoScalingRuleRow]:
        """Create multiple sample auto scaling rules for testing."""
        rules = []
        metric_names = ["cpu_util", "memory_util", "gpu_util", "request_rate", "latency"]

        for i, metric_name in enumerate(metric_names):
            rule = EndpointAutoScalingRuleRow(
                id=uuid.uuid4(),
                endpoint=sample_endpoint.id,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name=metric_name,
                threshold=50.0 + i * 10,
                comparator=AutoScalingMetricComparator.GREATER_THAN,
                step_size=1 + i,
                cooldown_seconds=300 + i * 60,
                min_replicas=1,
                max_replicas=10 + i,
                created_at=datetime.now(timezone.utc),
                endpoint_row=sample_endpoint,
            )
            rules.append(rule)

        return rules

    @pytest.fixture
    def sample_rules_for_pagination(self, sample_endpoint) -> list[EndpointAutoScalingRuleRow]:
        """Create 25 sample auto scaling rules for pagination testing."""
        rules = []

        for i in range(25):
            rule = EndpointAutoScalingRuleRow(
                id=uuid.uuid4(),
                endpoint=sample_endpoint.id,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name=f"metric_{i:02d}",
                threshold=50.0 + i,
                comparator=AutoScalingMetricComparator.GREATER_THAN,
                step_size=1,
                cooldown_seconds=300,
                min_replicas=1,
                max_replicas=10,
                created_at=datetime.now(timezone.utc),
                endpoint_row=sample_endpoint,
            )
            rules.append(rule)

        return rules

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _create_mock_batch_result(
        self,
        rules: list[EndpointAutoScalingRuleRow],
        total_count: int | None = None,
        has_next_page: bool = False,
        has_previous_page: bool = False,
    ) -> MagicMock:
        """Create a mock result for execute_batch_querier."""
        mock_rows = []
        for rule in rules:
            mock_row = MagicMock()
            mock_row.EndpointAutoScalingRuleRow = rule
            mock_rows.append(mock_row)

        mock_result = MagicMock()
        mock_result.rows = mock_rows
        mock_result.total_count = total_count if total_count is not None else len(rules)
        mock_result.has_next_page = has_next_page
        mock_result.has_previous_page = has_previous_page

        return mock_result

    # =========================================================================
    # Tests - Basic Search
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_force_success(
        self,
        admin_model_serving_repository: AdminModelServingRepository,
        setup_readonly_session,
        sample_auto_scaling_rules: list[EndpointAutoScalingRuleRow],
        mocker,
    ) -> None:
        """Test search without access validation (force)."""
        # Arrange
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.admin_repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(sample_auto_scaling_rules)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        # Act
        result = await admin_model_serving_repository.search_auto_scaling_rules_force(
            querier=querier,
        )

        # Assert
        assert result is not None
        assert isinstance(result, EndpointAutoScalingRuleListResult)
        assert len(result.items) == len(sample_auto_scaling_rules)
        mock_execute_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_force_empty_result(
        self,
        admin_model_serving_repository: AdminModelServingRepository,
        setup_readonly_session,
        mocker,
    ) -> None:
        """Test force search returns empty result when no rules exist."""
        # Arrange
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.admin_repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result([], total_count=0)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        # Act
        result = await admin_model_serving_repository.search_auto_scaling_rules_force(
            querier=querier,
        )

        # Assert
        assert result is not None
        assert len(result.items) == 0
        assert result.total_count == 0

    # =========================================================================
    # Tests - Pagination
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_force_with_pagination(
        self,
        admin_model_serving_repository: AdminModelServingRepository,
        setup_readonly_session,
        sample_rules_for_pagination: list[EndpointAutoScalingRuleRow],
        mocker,
    ) -> None:
        """Test force search with pagination."""
        # Arrange
        first_page_rules = sample_rules_for_pagination[:10]
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.admin_repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(
            first_page_rules,
            total_count=25,
            has_next_page=True,
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        # Act
        result = await admin_model_serving_repository.search_auto_scaling_rules_force(
            querier=querier,
        )

        # Assert
        assert len(result.items) == 10
        assert result.total_count == 25
        assert result.has_next_page is True

    # =========================================================================
    # Tests - Ordering
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_force_with_ordering(
        self,
        admin_model_serving_repository: AdminModelServingRepository,
        setup_readonly_session,
        sample_auto_scaling_rules: list[EndpointAutoScalingRuleRow],
        mocker,
    ) -> None:
        """Test force search with ordering."""
        # Arrange: Sort rules by metric_name ascending
        sorted_rules = sorted(sample_auto_scaling_rules, key=lambda r: r.metric_name)
        mock_execute_batch = mocker.patch(
            "ai.backend.manager.repositories.model_serving.admin_repository.execute_batch_querier",
            new_callable=AsyncMock,
        )
        mock_execute_batch.return_value = self._create_mock_batch_result(sorted_rules)

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[EndpointAutoScalingRuleRow.metric_name.asc()],
        )

        # Act
        result = await admin_model_serving_repository.search_auto_scaling_rules_force(
            querier=querier,
        )

        # Assert
        assert result is not None
        metric_names = [item.metric_name for item in result.items]
        assert metric_names == sorted(metric_names)
