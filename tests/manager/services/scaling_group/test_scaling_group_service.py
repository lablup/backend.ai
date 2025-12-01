"""
Tests for ScalingGroupService functionality.
Tests the service layer with mocked repository operations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.scaling_group.types import ScalingGroupData, ScalingGroupListResult
from ai.backend.manager.repositories.base import Querier
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
            description="Default scaling group",
            is_active=True,
            is_public=True,
            created_at=datetime.now(),
            wsproxy_addr="",
            wsproxy_api_token="",
            driver="static",
            driver_opts={},
            scheduler="fifo",
            scheduler_opts={},
            use_host_network=False,
        )

    @pytest.mark.asyncio
    async def test_search_scaling_groups_without_querier(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ScalingGroupData,
    ) -> None:
        """Test searching scaling groups without querier"""
        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=[sample_scaling_group],
                total_count=1,
            )
        )

        action = SearchScalingGroupsAction(querier=None)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.scaling_groups == [sample_scaling_group]
        assert result.total_count == 1
        mock_repository.search_scaling_groups.assert_called_once_with(querier=None)

    @pytest.mark.asyncio
    async def test_search_scaling_groups_with_querier(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ScalingGroupData,
    ) -> None:
        """Test searching scaling groups with querier"""
        querier = Querier(conditions=[], orders=[], pagination=None)
        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=[sample_scaling_group],
                total_count=1,
            )
        )

        action = SearchScalingGroupsAction(querier=querier)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.scaling_groups == [sample_scaling_group]
        assert result.total_count == 1
        mock_repository.search_scaling_groups.assert_called_once_with(querier=querier)

    @pytest.mark.asyncio
    async def test_search_scaling_groups_with_multiple_results(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching scaling groups with multiple results"""
        scaling_groups = [
            ScalingGroupData(
                name=f"sgroup-{i}",
                description=f"Scaling group {i}",
                is_active=True,
                is_public=True,
                created_at=datetime.now(),
                wsproxy_addr="",
                wsproxy_api_token="",
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts={},
                use_host_network=False,
            )
            for i in range(3)
        ]

        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=scaling_groups,
                total_count=3,
            )
        )

        action = SearchScalingGroupsAction(querier=None)
        result = await scaling_group_service.search_scaling_groups(action)

        assert len(result.scaling_groups) == 3
        assert result.total_count == 3
        assert result.scaling_groups == scaling_groups

    @pytest.mark.asyncio
    async def test_search_scaling_groups_with_empty_result(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching scaling groups with empty result"""
        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=[],
                total_count=0,
            )
        )

        action = SearchScalingGroupsAction(querier=None)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.scaling_groups == []
        assert result.total_count == 0
