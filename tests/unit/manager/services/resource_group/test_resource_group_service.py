"""
Tests for ResourceGroupService functionality.
Tests the service layer with mocked repository operations.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import ResourceGroupConflict
from ai.backend.common.types import AgentSelectionStrategy, ResourceSlot, SessionTypes
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.data.resource_group.types import (
    FairShareResourceGroupSpec,
    ResourceGroupData,
    ResourceGroupDriverConfig,
    ResourceGroupMetadata,
    ResourceGroupNetworkConfig,
    ResourceGroupSchedulerConfig,
    ResourceGroupSchedulerOptions,
    ResourceGroupStatus,
    SchedulerType,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.resource import (
    ResourceGroupNotFound,
    ResourceGroupSessionTypeNotAllowed,
)
from ai.backend.manager.models.resource_group import ResourceGroupOpts
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator
from ai.backend.manager.models.resource_group.scopes import UserResourceGroupTarget
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater
from ai.backend.manager.registry import check_resource_group
from ai.backend.manager.repositories.resource_group import ResourceGroupRepository
from ai.backend.manager.services.resource_group.actions.create import CreateResourceGroupAction
from ai.backend.manager.services.resource_group.actions.get_wsproxy_version import (
    GetWsproxyVersionAction,
)
from ai.backend.manager.services.resource_group.actions.update import (
    UpdateResourceGroupAction,
)
from ai.backend.manager.services.resource_group.service import (
    WSPROXY_V1_VERSION,
    ResourceGroupService,
)
from ai.backend.manager.types import OptionalState, TriState


class TestScalingGroupService:
    """Test cases for ResourceGroupService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked ResourceGroupRepository"""
        return MagicMock(spec=ResourceGroupRepository)

    @pytest.fixture
    def resource_group_service(self, mock_repository: MagicMock) -> ResourceGroupService:
        """Create ResourceGroupService instance with mocked repository"""
        return ResourceGroupService(repository=mock_repository)

    @pytest.fixture
    def sample_scaling_group(self) -> ResourceGroupData:
        """Create sample scaling group data"""
        return ResourceGroupData(
            id=ResourceGroupID(uuid.uuid4()),
            name="default",
            status=ResourceGroupStatus(
                is_active=True,
                is_public=True,
                is_default=False,
            ),
            metadata=ResourceGroupMetadata(
                description="Default scaling group",
                created_at=datetime.now(tz=UTC),
            ),
            network=ResourceGroupNetworkConfig(
                wsproxy_addr="",
                wsproxy_api_token="",
                use_host_network=False,
            ),
            driver=ResourceGroupDriverConfig(
                name="static",
                options={},
            ),
            scheduler=ResourceGroupSchedulerConfig(
                name=SchedulerType.FIFO,
                options=ResourceGroupSchedulerOptions(
                    allowed_session_types=[
                        SessionTypes.INTERACTIVE,
                        SessionTypes.BATCH,
                        SessionTypes.INFERENCE,
                    ],
                    pending_timeout=timedelta(seconds=0),
                    config={},
                    agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
                    agent_selector_config={},
                    allow_fractional_resource_fragmentation=True,
                    route_cleanup_target_statuses=["unhealthy"],
                ),
            ),
            fair_share_spec=FairShareResourceGroupSpec(
                half_life_days=7,
                lookback_days=28,
                decay_unit_days=1,
                default_weight=Decimal("1.0"),
                resource_weights=ResourceSlot(),
            ),
            default_deployment_options=DeploymentOptions(),
            default_session_options=DefaultSessionOptions(),
        )

    @pytest.fixture
    def resource_group_creator_full(self) -> ResourceGroupCreator:
        """Creator with full configuration for testing create_scaling_group success"""
        scheduler_opts = ResourceGroupOpts(
            allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
            pending_timeout=timedelta(seconds=300),
            config={"max_sessions": 10},
            agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
        )
        return ResourceGroupCreator(
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

    # Create Tests

    async def test_create_scaling_group_success(
        self,
        resource_group_service: ResourceGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ResourceGroupData,
        resource_group_creator_full: ResourceGroupCreator,
    ) -> None:
        """Test creating a scaling group successfully"""
        mock_repository.create_resource_group = AsyncMock(return_value=sample_scaling_group)

        action = CreateResourceGroupAction(creator=resource_group_creator_full)
        result = await resource_group_service.create_resource_group(action)

        assert result.resource_group == sample_scaling_group
        mock_repository.create_resource_group.assert_called_once_with(resource_group_creator_full)

    async def test_create_scaling_group_conflict(
        self,
        resource_group_service: ResourceGroupService,
        mock_repository: MagicMock,
        resource_group_creator_full: ResourceGroupCreator,
    ) -> None:
        """Test that ScalingGroupConflict propagates through the service"""
        mock_repository.create_resource_group = AsyncMock(
            side_effect=ResourceGroupConflict("Scaling group already exists: test-sgroup-full")
        )

        action = CreateResourceGroupAction(creator=resource_group_creator_full)

        with pytest.raises(ResourceGroupConflict):
            await resource_group_service.create_resource_group(action)

    # Modify Tests

    async def test_modify_scaling_group_success(
        self,
        resource_group_service: ResourceGroupService,
        mock_repository: MagicMock,
        sample_scaling_group: ResourceGroupData,
    ) -> None:
        """Test modifying a scaling group successfully"""
        mock_repository.update_resource_group = AsyncMock(return_value=sample_scaling_group)

        resource_group_id = ResourceGroupID(uuid.uuid4())
        updater = ResourceGroupUpdater(
            resource_group_id=resource_group_id,
            is_active=OptionalState.update(False),
            description=TriState.update("Updated description"),
        )
        action = UpdateResourceGroupAction(resource_group_id=resource_group_id, updater=updater)
        result = await resource_group_service.update_resource_group(action)

        assert result.resource_group == sample_scaling_group
        mock_repository.update_resource_group.assert_called_once_with(updater)

    async def test_modify_scaling_group_not_found(
        self,
        resource_group_service: ResourceGroupService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that ScalingGroupNotFound propagates through the service"""
        mock_repository.update_resource_group = AsyncMock(
            side_effect=ResourceGroupNotFound("Scaling group not found: nonexistent")
        )

        resource_group_id = ResourceGroupID(uuid.uuid4())
        updater = ResourceGroupUpdater(
            resource_group_id=resource_group_id,
            description=TriState.update("Updated description"),
        )
        action = UpdateResourceGroupAction(resource_group_id=resource_group_id, updater=updater)

        with pytest.raises(ResourceGroupNotFound):
            await resource_group_service.update_resource_group(action)


class TestCheckScalingGroup:
    """Test cases for check_scaling_group function"""

    @pytest.fixture
    def interactive_only_sgroup(self) -> MagicMock:
        """Create a scaling group accepting INTERACTIVE sessions only"""
        mock_sgroup = MagicMock()
        mock_sgroup.name = "test-sgroup"
        mock_sgroup.scheduler.options.allowed_session_types = [SessionTypes.INTERACTIVE]
        return mock_sgroup

    def test_check_scaling_group_raises_session_type_not_allowed(
        self,
        interactive_only_sgroup: MagicMock,
    ) -> None:
        """Test that check_scaling_group raises ResourceGroupSessionTypeNotAllowed (400)
        when requesting BATCH session on INTERACTIVE-only scaling group"""
        with pytest.raises(ResourceGroupSessionTypeNotAllowed) as exc_info:
            check_resource_group(
                [interactive_only_sgroup],
                resource_group="test-sgroup",
                session_type=SessionTypes.BATCH,
            )
        assert exc_info.value.status_code == 400

    def test_check_scaling_group_succeeds_with_allowed_session_type(
        self,
        interactive_only_sgroup: MagicMock,
    ) -> None:
        """Test that check_scaling_group succeeds when session type is allowed"""
        result = check_resource_group(
            [interactive_only_sgroup],
            resource_group="test-sgroup",
            session_type=SessionTypes.INTERACTIVE,
        )
        assert result == "test-sgroup"

    def test_check_scaling_group_raises_not_found(self) -> None:
        """Test that check_scaling_group raises ScalingGroupNotFound (404)
        when the scaling group does not exist"""
        with pytest.raises(ResourceGroupNotFound) as exc_info:
            check_resource_group(
                [],
                resource_group="nonexistent-sgroup",
                session_type=SessionTypes.INTERACTIVE,
            )
        assert exc_info.value.status_code == 404


class TestGetWsproxyVersion:
    """Tests for ResourceGroupService.get_wsproxy_version"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=ResourceGroupRepository)

    @pytest.fixture
    def mock_appproxy_client_pool(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def resource_group_service(
        self,
        mock_repository: MagicMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> ResourceGroupService:
        return ResourceGroupService(
            repository=mock_repository,
            appproxy_client_pool=mock_appproxy_client_pool,
        )

    @pytest.fixture
    def sample_sgroup_with_wsproxy(self) -> ResourceGroupData:
        return ResourceGroupData(
            id=ResourceGroupID(uuid.uuid4()),
            name="gpu-group",
            status=ResourceGroupStatus(is_active=True, is_public=True, is_default=False),
            metadata=ResourceGroupMetadata(
                description="GPU group",
                created_at=datetime.now(tz=UTC),
            ),
            network=ResourceGroupNetworkConfig(
                wsproxy_addr="http://wsproxy:5000",
                wsproxy_api_token="test-token",
                use_host_network=False,
            ),
            driver=ResourceGroupDriverConfig(name="static", options={}),
            scheduler=ResourceGroupSchedulerConfig(
                name=SchedulerType.FIFO,
                options=ResourceGroupSchedulerOptions(
                    allowed_session_types=[SessionTypes.INTERACTIVE],
                    pending_timeout=timedelta(seconds=0),
                    config={},
                    agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
                    agent_selector_config={},
                    allow_fractional_resource_fragmentation=True,
                    route_cleanup_target_statuses=["unhealthy"],
                ),
            ),
            fair_share_spec=FairShareResourceGroupSpec(
                half_life_days=7,
                lookback_days=28,
                decay_unit_days=1,
                default_weight=Decimal("1.0"),
                resource_weights=ResourceSlot(),
            ),
            default_deployment_options=DeploymentOptions(),
            default_session_options=DefaultSessionOptions(),
        )

    async def test_accessible_scaling_group_returns_version(
        self,
        resource_group_service: ResourceGroupService,
        mock_repository: MagicMock,
        mock_appproxy_client_pool: MagicMock,
        sample_sgroup_with_wsproxy: ResourceGroupData,
    ) -> None:
        """Accessible scaling group returns wsproxy version string."""
        mock_repository.list_active_resource_groups = AsyncMock(
            return_value=[sample_sgroup_with_wsproxy]
        )
        mock_client = AsyncMock()
        mock_status = MagicMock()
        mock_status.api_version = "v2.0.0"
        mock_client.fetch_status = AsyncMock(return_value=mock_status)
        mock_appproxy_client_pool.load_client.return_value = mock_client

        action = GetWsproxyVersionAction(
            resource_group_name="gpu-group",
            targets=[UserResourceGroupTarget(user_id=UserID(uuid.uuid4()))],
        )

        result = await resource_group_service.get_wsproxy_version(action)

        assert result.wsproxy_version == "v2.0.0"
        mock_appproxy_client_pool.load_client.assert_called_once_with(
            "http://wsproxy:5000", "test-token"
        )

    async def test_non_allowed_group_raises_object_not_found(
        self,
        resource_group_service: ResourceGroupService,
        mock_repository: MagicMock,
    ) -> None:
        """Non-allowed scaling group raises ResourceGroupNotFound."""
        mock_repository.list_active_resource_groups = AsyncMock(return_value=[])

        action = GetWsproxyVersionAction(
            resource_group_name="nonexistent-group",
            targets=[UserResourceGroupTarget(user_id=UserID(uuid.uuid4()))],
        )

        with pytest.raises(ResourceGroupNotFound):
            await resource_group_service.get_wsproxy_version(action)

    async def test_wsproxy_addr_not_set_returns_v1(
        self,
        resource_group_service: ResourceGroupService,
        mock_repository: MagicMock,
        sample_sgroup_with_wsproxy: ResourceGroupData,
    ) -> None:
        """wsproxy_addr not set returns v1 version."""
        no_wsproxy = ResourceGroupData(
            id=ResourceGroupID(uuid.uuid4()),
            name="gpu-group",
            status=sample_sgroup_with_wsproxy.status,
            metadata=sample_sgroup_with_wsproxy.metadata,
            network=ResourceGroupNetworkConfig(
                wsproxy_addr="",
                wsproxy_api_token="",
                use_host_network=False,
            ),
            driver=sample_sgroup_with_wsproxy.driver,
            scheduler=sample_sgroup_with_wsproxy.scheduler,
            fair_share_spec=sample_sgroup_with_wsproxy.fair_share_spec,
            default_deployment_options=DeploymentOptions(),
            default_session_options=DefaultSessionOptions(),
        )
        mock_repository.list_active_resource_groups = AsyncMock(return_value=[no_wsproxy])

        action = GetWsproxyVersionAction(
            resource_group_name="gpu-group",
            targets=[UserResourceGroupTarget(user_id=UserID(uuid.uuid4()))],
        )

        result = await resource_group_service.get_wsproxy_version(action)
        assert result.wsproxy_version == WSPROXY_V1_VERSION

    async def test_appproxy_pool_none_raises_object_not_found(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """AppProxy client pool not available raises ObjectNotFound."""
        service = ResourceGroupService(repository=mock_repository, appproxy_client_pool=None)

        action = GetWsproxyVersionAction(
            resource_group_name="gpu-group",
            targets=[UserResourceGroupTarget(user_id=UserID(uuid.uuid4()))],
        )

        with pytest.raises(ObjectNotFound):
            await service.get_wsproxy_version(action)
