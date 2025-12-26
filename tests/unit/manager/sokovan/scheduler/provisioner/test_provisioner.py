"""Tests for SessionProvisioner orchestration logic.

Tests that the provisioner correctly orchestrates validator, sequencer, selector, and allocator.
Individual component logic is tested separately - here we focus on orchestration flow
and correct agent selector selection based on agent_selection_strategy.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.agent import AgentMeta
from ai.backend.manager.repositories.scheduler.types.base import SchedulingSpec
from ai.backend.manager.repositories.scheduler.types.scaling_group import ScalingGroupMeta
from ai.backend.manager.repositories.scheduler.types.scheduling import SchedulingData
from ai.backend.manager.repositories.scheduler.types.session import (
    PendingSessionData,
    PendingSessions,
)
from ai.backend.manager.repositories.scheduler.types.snapshot import (
    ResourcePolicies,
    SnapshotData,
)
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
    SessionProvisioner,
    SessionProvisionerArgs,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelector,
)
from ai.backend.manager.sokovan.scheduler.types import (
    ResourceOccupancySnapshot,
    SessionDependencySnapshot,
)


def _create_scheduling_data_with_strategy(
    strategy: AgentSelectionStrategy,
) -> SchedulingData:
    """Create SchedulingData with specific agent_selection_strategy and one session."""
    scheduler_opts = ScalingGroupOpts(agent_selection_strategy=strategy)

    scaling_group_meta = ScalingGroupMeta(
        name="test-sg",
        scheduler="fifo",
        scheduler_opts=scheduler_opts,
    )

    # Create one pending session
    session = PendingSessionData(
        id=SessionId(uuid.uuid4()),
        access_key=AccessKey("test-key"),
        requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
        user_uuid=uuid.uuid4(),
        group_id=uuid.uuid4(),
        domain_name="default",
        scaling_group_name="test-sg",
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        priority=0,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
    )

    # Create snapshot data
    snapshot_data = SnapshotData(
        resource_occupancy=ResourceOccupancySnapshot(
            by_keypair={},
            by_user={},
            by_group={},
            by_domain={},
            by_agent={},
        ),
        resource_policies=ResourcePolicies(
            keypair_policies={},
            user_policies={},
            group_limits={},
            domain_limits={},
        ),
        session_dependencies=SessionDependencySnapshot(by_session={}),
    )

    # Create agent
    agent = AgentMeta(
        id=AgentId("agent-1"),
        addr="agent-1:6001",
        architecture="x86_64",
        available_slots=ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("16384")}),
        scaling_group="test-sg",
    )

    return SchedulingData(
        scaling_group=scaling_group_meta,
        pending_sessions=PendingSessions(sessions=[session]),
        agents=[agent],
        snapshot_data=snapshot_data,
        spec=SchedulingSpec(
            known_slot_types={},
            max_container_count=None,
        ),
    )


@pytest.fixture
def minimal_scheduling_data() -> SchedulingData:
    """Create minimal SchedulingData for testing."""
    scheduler_opts = ScalingGroupOpts(agent_selection_strategy=AgentSelectionStrategy.DISPERSED)

    scaling_group_meta = ScalingGroupMeta(
        name="test-sg",
        scheduler="fifo",
        scheduler_opts=scheduler_opts,
    )

    return SchedulingData(
        scaling_group=scaling_group_meta,
        pending_sessions=PendingSessions(sessions=[]),
        agents=[],
        snapshot_data=None,
        spec=SchedulingSpec(
            known_slot_types={},
            max_container_count=None,
        ),
    )


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Create mock config provider."""
    mock_config = MagicMock()
    mock_config.config.manager.agent_selection_resource_priority = ["cpu", "mem"]
    return mock_config


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create mock repository."""
    return AsyncMock()


@pytest.fixture
def mock_validator() -> MagicMock:
    """Create mock validator."""
    validator = MagicMock()
    validator.validate = MagicMock(return_value=None)
    return validator


@pytest.fixture
def mock_sequencer() -> MagicMock:
    """Create mock sequencer."""
    sequencer = MagicMock()
    sequencer.sequence = MagicMock(return_value=[])
    sequencer.name = "test-sequencer"
    sequencer.success_message = MagicMock(return_value="Sequencing succeeded")
    return sequencer


@pytest.fixture
def mock_agent_selector() -> MagicMock:
    """Create mock agent selector."""
    selector = MagicMock()
    selector.select_agents_for_batch_requirements = AsyncMock(return_value=[])
    selector.strategy_name = MagicMock(return_value="test-strategy")
    selector.strategy_success_message = MagicMock(return_value="Agent selection succeeded")
    return selector


@pytest.fixture
def mock_allocator() -> MagicMock:
    """Create mock allocator."""
    allocator = MagicMock()
    allocator.allocate = AsyncMock(return_value=[])
    allocator.name = MagicMock(return_value="test-allocator")
    allocator.success_message = MagicMock(return_value="Allocation succeeded")
    return allocator


@pytest.fixture
def mock_selector_pool() -> dict[AgentSelectionStrategy, MagicMock]:
    """Create mock selector pool for all strategies."""
    mock_selectors = {s: MagicMock(spec=AgentSelector) for s in AgentSelectionStrategy}

    for mock_selector in mock_selectors.values():
        mock_selector.select_agents_for_batch_requirements = AsyncMock(return_value=[])
        mock_selector.strategy_name = MagicMock(return_value="test-strategy")
        mock_selector.strategy_success_message = MagicMock(return_value="Selection succeeded")

    return mock_selectors


@pytest.fixture
def test_provisioner(
    mock_repository: AsyncMock,
    mock_validator: MagicMock,
    mock_sequencer: MagicMock,
    mock_agent_selector: MagicMock,
    mock_allocator: MagicMock,
    mock_config_provider: MagicMock,
) -> SessionProvisioner:
    """Create SessionProvisioner with mock dependencies."""
    valkey_schedule = MagicMock()
    valkey_schedule.set_pending_queue = AsyncMock(return_value=None)

    return SessionProvisioner(
        SessionProvisionerArgs(
            validator=mock_validator,
            default_sequencer=mock_sequencer,
            default_agent_selector=mock_agent_selector,
            allocator=mock_allocator,
            repository=mock_repository,
            config_provider=mock_config_provider,
            valkey_schedule=valkey_schedule,
        )
    )


class TestScheduleQueuedSessionsWithData:
    """Test _schedule_queued_sessions_with_data method."""

    @pytest.mark.parametrize(
        "strategy",
        [
            AgentSelectionStrategy.DISPERSED,
            AgentSelectionStrategy.CONCENTRATED,
            AgentSelectionStrategy.ROUNDROBIN,
            AgentSelectionStrategy.LEGACY,
        ],
    )
    async def test_uses_correct_agent_selector(
        self,
        strategy: AgentSelectionStrategy,
        test_provisioner: SessionProvisioner,
        mock_selector_pool: dict[AgentSelectionStrategy, MagicMock],
    ) -> None:
        """
        Verify that _schedule_queued_sessions_with_data uses correct agent_selector.
        """
        # Given: Override provisioner's selector pool with mock selectors
        test_provisioner._agent_selector_pool = mock_selector_pool

        # Given: SchedulingData with specific strategy
        scheduling_data = _create_scheduling_data_with_strategy(strategy)

        # When: Execute _schedule_queued_sessions_with_data
        await test_provisioner._schedule_queued_sessions_with_data("test-sg", scheduling_data)

        # Then: The selector for the specified strategy was used
        used_selector = mock_selector_pool[strategy]
        used_selector.select_agents_for_batch_requirements.assert_called()

        # And: Other selectors were not used
        for other_strategy, other_selector in mock_selector_pool.items():
            if other_strategy != strategy:
                other_selector.select_agents_for_batch_requirements.assert_not_called()
