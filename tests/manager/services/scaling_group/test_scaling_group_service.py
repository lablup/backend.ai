"""
Tests for ScalingGroupService functionality.
Tests the service layer with mocked repository operations.
"""

from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import ScalingGroupConflict
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
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.repositories.scaling_group.creators import ScalingGroupCreatorSpec
from ai.backend.manager.services.scaling_group.actions.create import (
    CreateScalingGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


class TestScalingGroupService:
    """Test cases for ScalingGroupService"""

    def _create_scaling_group_creator(
        self,
        name: str,
        driver: str = "static",
        scheduler: str = "fifo",
        description: Optional[str] = None,
        is_active: bool = True,
        is_public: bool = True,
        wsproxy_addr: Optional[str] = None,
        wsproxy_api_token: Optional[str] = None,
        driver_opts: Optional[dict] = None,
        scheduler_opts: Optional[ScalingGroupOpts] = None,
        use_host_network: bool = False,
    ) -> Creator[ScalingGroupRow]:
        """Create a ScalingGroupCreatorSpec with the given parameters."""
        spec = ScalingGroupCreatorSpec(
            name=name,
            driver=driver,
            scheduler=scheduler,
            description=description,
            is_active=is_active,
            is_public=is_public,
            wsproxy_addr=wsproxy_addr,
            wsproxy_api_token=wsproxy_api_token,
            driver_opts=driver_opts if driver_opts is not None else {},
            scheduler_opts=scheduler_opts,
            use_host_network=use_host_network,
        )
        return Creator(spec=spec)

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

    async def test_search_scaling_groups_with_default_querier(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ScalingGroupData,
    ) -> None:
        """Test searching scaling groups with default querier"""
        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=[sample_scaling_group],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchScalingGroupsAction(querier=querier)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.scaling_groups == [sample_scaling_group]
        assert result.total_count == 1
        mock_repository.search_scaling_groups.assert_called_once_with(querier=querier)

    async def test_search_scaling_groups_with_querier(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ScalingGroupData,
    ) -> None:
        """Test searching scaling groups with querier"""
        from ai.backend.manager.repositories.base import OffsetPagination

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=[sample_scaling_group],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchScalingGroupsAction(querier=querier)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.scaling_groups == [sample_scaling_group]
        assert result.total_count == 1
        mock_repository.search_scaling_groups.assert_called_once_with(querier=querier)

    async def test_search_scaling_groups_with_multiple_results(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching scaling groups with multiple results"""
        scaling_groups = [
            ScalingGroupData(
                name=f"sgroup-{i}",
                status=ScalingGroupStatus(
                    is_active=True,
                    is_public=True,
                ),
                metadata=ScalingGroupMetadata(
                    description=f"Scaling group {i}",
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
            for i in range(3)
        ]

        mock_repository.search_scaling_groups = AsyncMock(
            return_value=ScalingGroupListResult(
                items=scaling_groups,
                total_count=3,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchScalingGroupsAction(querier=querier)
        result = await scaling_group_service.search_scaling_groups(action)

        assert len(result.scaling_groups) == 3
        assert result.total_count == 3
        assert result.scaling_groups == scaling_groups

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
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchScalingGroupsAction(querier=querier)
        result = await scaling_group_service.search_scaling_groups(action)

        assert result.scaling_groups == []
        assert result.total_count == 0

    async def test_create_scaling_group_success(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ScalingGroupData,
    ) -> None:
        """Test creating a scaling group with all fields specified"""
        mock_repository.create_scaling_group = AsyncMock(return_value=sample_scaling_group)

        scheduler_opts = ScalingGroupOpts(
            allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
            pending_timeout=timedelta(seconds=300),
            config={"max_sessions": 10},
            agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
        )
        creator = self._create_scaling_group_creator(
            name="test-sgroup-full",
            driver="docker",
            scheduler="fifo",
            description="Full test scaling group",
            is_active=True,
            is_public=False,
            wsproxy_addr="http://wsproxy:5000",
            wsproxy_api_token="test-token",
            driver_opts={"docker_host": "unix:///var/run/docker.sock"},
            scheduler_opts=scheduler_opts,
            use_host_network=True,
        )
        action = CreateScalingGroupAction(creator=creator)
        result = await scaling_group_service.create_scaling_group(action)

        assert result.scaling_group == sample_scaling_group
        mock_repository.create_scaling_group.assert_called_once_with(creator)

    @pytest.mark.asyncio
    async def test_create_scaling_group_with_minimal_fields(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ScalingGroupData,
    ) -> None:
        """Test creating a scaling group with only required fields"""
        mock_repository.create_scaling_group = AsyncMock(return_value=sample_scaling_group)

        spec = ScalingGroupCreatorSpec(
            name="test-sgroup-minimal",
            driver="static",
            scheduler="fifo",
        )
        creator: Creator[ScalingGroupRow] = Creator(spec=spec)
        action = CreateScalingGroupAction(creator=creator)
        result = await scaling_group_service.create_scaling_group(action)

        assert result.scaling_group == sample_scaling_group
        mock_repository.create_scaling_group.assert_called_once_with(creator)

    @pytest.mark.asyncio
    async def test_create_scaling_group_repository_error_propagates(
        self,
        scaling_group_service: ScalingGroupService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that repository errors propagate through the service"""
        mock_repository.create_scaling_group = AsyncMock(
            side_effect=ScalingGroupConflict("Scaling group already exists")
        )

        spec = ScalingGroupCreatorSpec(
            name="test-sgroup-conflict",
            driver="static",
            scheduler="fifo",
        )
        creator: Creator[ScalingGroupRow] = Creator(spec=spec)
        action = CreateScalingGroupAction(creator=creator)

        with pytest.raises(ScalingGroupConflict):
            await scaling_group_service.create_scaling_group(action)
