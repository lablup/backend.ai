"""
Tests for ScalingGroupService functionality.
Tests the service layer with mocked repository operations.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.exception import ScalingGroupConflict
from ai.backend.common.types import AccessKey, AgentSelectionStrategy, SessionTypes
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
from ai.backend.manager.errors.resource import (
    ScalingGroupNotFound,
    ScalingGroupSessionTypeNotAllowed,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.registry import check_scaling_group
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

    @pytest.fixture
    def scaling_group_creator_full(self) -> Creator[ScalingGroupRow]:
        """Creator with full configuration for testing create_scaling_group success"""
        scheduler_opts = ScalingGroupOpts(
            allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
            pending_timeout=timedelta(seconds=300),
            config={"max_sessions": 10},
            agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
        )
        spec = ScalingGroupCreatorSpec(
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
        return Creator(spec=spec)

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
        scaling_group_creator_full: Creator[ScalingGroupRow],
    ) -> None:
        """Test creating a scaling group with all fields specified"""
        mock_repository.create_scaling_group = AsyncMock(return_value=sample_scaling_group)

        action = CreateScalingGroupAction(creator=scaling_group_creator_full)
        result = await scaling_group_service.create_scaling_group(action)

        assert result.scaling_group == sample_scaling_group
        mock_repository.create_scaling_group.assert_called_once_with(scaling_group_creator_full)

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


class TestCheckScalingGroup:
    """Test cases for check_scaling_group function"""

    @pytest.fixture
    def mock_conn(self) -> MagicMock:
        """Create mocked database connection"""
        return MagicMock()

    async def test_check_scaling_group_raises_session_type_not_allowed(
        self,
        mock_conn: MagicMock,
    ) -> None:
        """Test that check_scaling_group raises ScalingGroupSessionTypeNotAllowed (422)
        when requesting BATCH session on INTERACTIVE-only scaling group"""
        mock_sgroup = {
            "name": "test-sgroup",
            "scheduler_opts": ScalingGroupOpts(
                allowed_session_types=[SessionTypes.INTERACTIVE],
            ),
        }

        with patch(
            "ai.backend.manager.registry.query_allowed_sgroups",
            new_callable=AsyncMock,
            return_value=[mock_sgroup],
        ):
            with pytest.raises(ScalingGroupSessionTypeNotAllowed) as exc_info:
                await check_scaling_group(
                    mock_conn,
                    scaling_group="test-sgroup",
                    session_type=SessionTypes.BATCH,
                    access_key=AccessKey("test-ak"),
                    domain_name="test-domain",
                    group_id="test-group-id",
                )
            assert exc_info.value.status_code == 422

    async def test_check_scaling_group_succeeds_with_allowed_session_type(
        self,
        mock_conn: MagicMock,
    ) -> None:
        """Test that check_scaling_group succeeds when session type is allowed"""
        mock_sgroup = {
            "name": "test-sgroup",
            "scheduler_opts": ScalingGroupOpts(
                allowed_session_types=[SessionTypes.INTERACTIVE],
            ),
        }

        with patch(
            "ai.backend.manager.registry.query_allowed_sgroups",
            new_callable=AsyncMock,
            return_value=[mock_sgroup],
        ):
            result = await check_scaling_group(
                mock_conn,
                scaling_group="test-sgroup",
                session_type=SessionTypes.INTERACTIVE,
                access_key=AccessKey("test-ak"),
                domain_name="test-domain",
                group_id="test-group-id",
            )
            assert result == "test-sgroup"

    async def test_check_scaling_group_raises_not_found(
        self,
        mock_conn: MagicMock,
    ) -> None:
        """Test that check_scaling_group raises ScalingGroupNotFound (404)
        when the scaling group does not exist"""
        with patch(
            "ai.backend.manager.registry.query_allowed_sgroups",
            new_callable=AsyncMock,
            return_value=[],
        ):
            with pytest.raises(ScalingGroupNotFound) as exc_info:
                await check_scaling_group(
                    mock_conn,
                    scaling_group="nonexistent-sgroup",
                    session_type=SessionTypes.INTERACTIVE,
                    access_key=AccessKey("test-ak"),
                    domain_name="test-domain",
                    group_id="test-group-id",
                )
            assert exc_info.value.status_code == 404
