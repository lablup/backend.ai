"""
Tests for ScalingGroupService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AgentSelectionStrategy, SessionTypes
from ai.backend.manager.data.scaling_group.types import (
    ScalingGroupData,
    ScalingGroupDriverConfig,
    ScalingGroupListResult,
    ScalingGroupMetadata,
    ScalingGroupNetworkConfig,
    ScalingGroupSchedulerConfig,
    ScalingGroupSchedulerOptions,
    ScalingGroupStatus,
    SchedulerType,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


class TestScalingGroupService:
    """Test cases for ScalingGroupService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked ScalingGroupRepository"""
        return MagicMock(spec=ScalingGroupRepository)

    @pytest.fixture
    def scaling_group_service(self, mock_repository: MagicMock) -> ScalingGroupService:
        """Create ScalingGroupService instance with mocked repository"""
        return ScalingGroupService(repository=mock_repository)

    @pytest.fixture
    def sample_scaling_group(self) -> ScalingGroupData:
        """Create sample scaling group data"""
        return ScalingGroupData(
            name="default",
            status=ScalingGroupStatus(
                is_active=True,
                is_public=True,
            ),
            metadata=ScalingGroupMetadata(
                description="Default scaling group",
                created_at=datetime.now(),
            ),
            network=ScalingGroupNetworkConfig(
                wsproxy_addr="",
                wsproxy_api_token="",
                use_host_network=False,
            ),
            driver=ScalingGroupDriverConfig(
                name="static",
                options={},
            ),
            scheduler=ScalingGroupSchedulerConfig(
                name=SchedulerType.FIFO,
                options=ScalingGroupSchedulerOptions(
                    allowed_session_types=[
                        SessionTypes.INTERACTIVE,
                        SessionTypes.BATCH,
                        SessionTypes.INFERENCE,
                    ],
                    pending_timeout=timedelta(seconds=0),
                    config={},
                    agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
                    agent_selector_config={},
                    enforce_spreading_endpoint_replica=False,
                    allow_fractional_resource_fragmentation=True,
                    route_cleanup_target_statuses=["unhealthy"],
                ),
            ),
        )

    async def test_search_scaling_groups(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ScalingGroupData,
    ) -> None:
        """Test searching scaling groups with querier"""
        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=[sample_scaling_group],
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
        action = SearchScalingGroupsAction(querier=querier)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.scaling_groups == [sample_scaling_group]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search_scaling_groups.assert_called_once_with(querier=querier)

    async def test_search_scaling_groups_empty_result(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching scaling groups when no results are found"""
        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
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
        action = SearchScalingGroupsAction(querier=querier)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.scaling_groups == []
        assert result.total_count == 0

    async def test_search_scaling_groups_with_pagination(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ScalingGroupData,
    ) -> None:
        """Test searching scaling groups with pagination"""
        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=[sample_scaling_group],
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
        action = SearchScalingGroupsAction(querier=querier)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
