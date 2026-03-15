"""Unit tests for PreemptSessionsLifecycleHandler."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    KernelId,
    PreemptionMode,
    PreemptionOrder,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
    SlotQuantity,
)
from ai.backend.manager.data.kernel.types import (
    ClusterConfig,
    ImageInfo,
    KernelInfo,
    KernelStatus,
    NetworkConfig,
    RelatedSessionInfo,
    ResourceInfo,
    RuntimeConfig,
    UserPermission,
)
from ai.backend.manager.data.kernel.types import LifecycleStatus as KernelLifecycleStatus
from ai.backend.manager.data.kernel.types import Metadata as KernelMetadata
from ai.backend.manager.data.kernel.types import Metrics as KernelMetrics
from ai.backend.manager.data.session.types import (
    ImageSpec,
    MountSpec,
    ResourceSpec,
    SessionExecution,
    SessionIdentity,
    SessionInfo,
    SessionLifecycle,
    SessionMetadata,
    SessionMetrics,
    SessionNetwork,
    SessionStatus,
)
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.scaling_group.row import PreemptionConfig, ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.agent import AgentMeta
from ai.backend.manager.repositories.scheduler.types.base import SchedulingSpec
from ai.backend.manager.repositories.scheduler.types.scaling_group import ScalingGroupMeta
from ai.backend.manager.repositories.scheduler.types.scheduling import SchedulingData
from ai.backend.manager.repositories.scheduler.types.session import PendingSessions
from ai.backend.manager.repositories.scheduler.types.snapshot import ResourcePolicies, SnapshotData
from ai.backend.manager.sokovan.data import (
    AgentOccupancy,
    ResourceOccupancySnapshot,
    RunningSessionData,
    SessionDependencySnapshot,
    SessionWithKernels,
)
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.preempt_sessions import (
    PreemptSessionsLifecycleHandler,
)


def _create_session(
    status: SessionStatus = SessionStatus.PENDING,
    scaling_group: str = "default",
    access_key: str = "test-access-key",
) -> SessionWithKernels:
    """Create a minimal SessionWithKernels for preemption handler tests."""
    sid = SessionId(uuid4())
    creation_id = str(uuid4())
    user_uuid = uuid4()
    group_id = uuid4()
    now = datetime.now(tzutc())
    kernel_id = KernelId(uuid4())
    agent_id = AgentId("agent-0")

    session_info = SessionInfo(
        identity=SessionIdentity(
            id=sid,
            creation_id=creation_id,
            name=f"session-{sid}",
            session_type=SessionTypes.INTERACTIVE,
            priority=0,
        ),
        metadata=SessionMetadata(
            name=f"session-{sid}",
            domain_name="default",
            group_id=group_id,
            user_uuid=user_uuid,
            access_key=access_key,
            session_type=SessionTypes.INTERACTIVE,
            priority=0,
            created_at=now,
            tag=None,
        ),
        resource=ResourceSpec(
            cluster_mode=ClusterMode.SINGLE_NODE.value,
            cluster_size=1,
            occupying_slots=ResourceSlot(),
            requested_slots=ResourceSlot(),
            scaling_group_name=scaling_group,
            target_sgroup_names=None,
            agent_ids=None,
        ),
        image=ImageSpec(images=["test-image:latest"], tag=None),
        mounts=MountSpec(vfolder_mounts=None),
        execution=SessionExecution(
            environ=None,
            bootstrap_script=None,
            startup_command=None,
            use_host_network=False,
            callback_url=None,
        ),
        lifecycle=SessionLifecycle(
            status=status,
            result=SessionResult.UNDEFINED,
            created_at=now,
            terminated_at=None,
            starts_at=None,
            status_changed=now,
            batch_timeout=None,
            status_info=None,
            status_data=None,
            status_history=None,
        ),
        metrics=SessionMetrics(num_queries=0, last_stat=None),
        network=SessionNetwork(network_type=None, network_id=None),
    )

    kernel_info = KernelInfo(
        id=kernel_id,
        session=RelatedSessionInfo(
            session_id=str(sid),
            creation_id=creation_id,
            name=f"session-{sid}",
            session_type=SessionTypes.INTERACTIVE,
        ),
        user_permission=UserPermission(
            user_uuid=user_uuid,
            access_key=access_key,
            domain_name="default",
            group_id=group_id,
            uid=None,
            main_gid=None,
            gids=None,
        ),
        image=ImageInfo(
            identifier=None,
            registry="docker.io",
            tag="latest",
            architecture="x86_64",
        ),
        network=NetworkConfig(
            kernel_host=None,
            repl_in_port=2000,
            repl_out_port=2001,
            stdin_port=2002,
            stdout_port=2003,
            service_ports=None,
            preopen_ports=None,
            use_host_network=False,
        ),
        cluster=ClusterConfig(
            cluster_mode=ClusterMode.SINGLE_NODE.value,
            cluster_size=1,
            cluster_role=DEFAULT_ROLE,
            cluster_idx=0,
            local_rank=0,
            cluster_hostname="kernel-0",
        ),
        resource=ResourceInfo(
            scaling_group=scaling_group,
            agent=agent_id,
            agent_addr="tcp://agent-0:5001",
            container_id=f"container-{kernel_id}",
            occupied_slots=ResourceSlot(),
            requested_slots=ResourceSlot(),
            occupied_shares={},
            attached_devices={},
            resource_opts={},
        ),
        runtime=RuntimeConfig(
            environ=None,
            mounts=None,
            mount_map=None,
            vfolder_mounts=None,
            bootstrap_script=None,
            startup_command=None,
        ),
        lifecycle=KernelLifecycleStatus(
            status=KernelStatus.PENDING,
            result=SessionResult.UNDEFINED,
            created_at=now,
            terminated_at=None,
            starts_at=None,
            status_changed=now,
            status_info=None,
            status_data=None,
            status_history=None,
            last_seen=None,
            last_observed_at=None,
        ),
        metrics=KernelMetrics(num_queries=0, last_stat=None, container_log=None),
        metadata=KernelMetadata(callback_url=None, internal_data=None),
    )

    return SessionWithKernels(
        session_info=session_info,
        kernel_infos=[kernel_info],
        phase_attempts=0,
        phase_started_at=None,
    )


def _make_running_session(
    priority: int = 3,
    is_preemptible: bool = True,
    cpu: str = "2",
    mem: str = "4096",
    created_at: datetime | None = None,
) -> RunningSessionData:
    return RunningSessionData(
        session_id=SessionId(uuid4()),
        access_key=AccessKey("test-key"),
        priority=priority,
        is_preemptible=is_preemptible,
        occupied_slots=ResourceSlot({"cpu": Decimal(cpu), "mem": Decimal(mem)}),
        created_at=created_at or datetime.now(tzutc()),
        scaling_group_name="default",
    )


def _make_scheduling_data(
    total_cpu: str = "8",
    total_mem: str = "16384",
    occupied_cpu: str = "6",
    occupied_mem: str = "12288",
    preemptible_priority: int = 5,
    preemption_order: PreemptionOrder = PreemptionOrder.OLDEST,
    preemption_mode: PreemptionMode = PreemptionMode.TERMINATE,
) -> SchedulingData:
    """Create a SchedulingData with preemption config and resource state."""
    preemption_config = PreemptionConfig(
        preemptible_priority=preemptible_priority,
        order=preemption_order,
        mode=preemption_mode,
    )
    scaling_group_meta = ScalingGroupMeta(
        name="default",
        scheduler="fifo",
        scheduler_opts=ScalingGroupOpts(preemption=preemption_config),
    )
    agent_id = AgentId("agent-0")
    agent = AgentMeta(
        id=agent_id,
        addr="tcp://agent-0:5001",
        architecture="x86_64",
        available_slots=ResourceSlot({"cpu": Decimal(total_cpu), "mem": Decimal(total_mem)}),
        scaling_group="default",
    )
    # We express occupied slots through the ResourceOccupancySnapshot
    occupancy = AgentOccupancy(
        occupied_slots=[
            SlotQuantity(slot_name="cpu", quantity=Decimal(occupied_cpu)),
            SlotQuantity(slot_name="mem", quantity=Decimal(occupied_mem)),
        ],
        container_count=2,
    )
    resource_occupancy = ResourceOccupancySnapshot(
        by_keypair={},
        by_user={},
        by_group={},
        by_domain={},
        by_agent={agent_id: occupancy},
    )
    snapshot_data = SnapshotData(
        resource_occupancy=resource_occupancy,
        resource_policies=ResourcePolicies(
            keypair_policies={},
            user_policies={},
            group_limits={},
            domain_limits={},
        ),
        session_dependencies=SessionDependencySnapshot(by_session={}),
    )
    return SchedulingData(
        scaling_group=scaling_group_meta,
        pending_sessions=PendingSessions(sessions=[]),
        agents=[agent],
        snapshot_data=snapshot_data,
        spec=SchedulingSpec(known_slot_types={}),
    )


class TestPreemptSessionsLifecycleHandler:
    """Tests for PreemptSessionsLifecycleHandler."""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        repo = AsyncMock()
        repo.get_scheduling_data = AsyncMock(return_value=None)
        repo.get_running_sessions_for_preemption = AsyncMock(return_value=[])
        repo.mark_sessions_terminating = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def handler(self, mock_repository: AsyncMock) -> PreemptSessionsLifecycleHandler:
        return PreemptSessionsLifecycleHandler(repository=mock_repository)

    async def test_no_sessions_returns_empty_result(
        self,
        handler: PreemptSessionsLifecycleHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Empty session list → no preemption attempted."""
        result = await handler.execute("default", [])
        assert result.successes == []
        mock_repository.mark_sessions_terminating.assert_not_called()

    async def test_no_preemption_when_scheduling_data_is_none(
        self,
        handler: PreemptSessionsLifecycleHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """If get_scheduling_data returns None, skip preemption."""
        mock_repository.get_scheduling_data.return_value = None
        pending = _create_session(status=SessionStatus.PENDING)

        result = await handler.execute("default", [pending])
        assert result.successes == []
        mock_repository.mark_sessions_terminating.assert_not_called()

    async def test_no_preemption_when_mode_is_not_terminate(
        self,
        handler: PreemptSessionsLifecycleHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Preemption is skipped when preemption_mode != TERMINATE."""
        scheduling_data = _make_scheduling_data(preemption_mode=PreemptionMode.RESCHEDULE)
        mock_repository.get_scheduling_data.return_value = scheduling_data
        pending = _create_session(status=SessionStatus.PENDING)

        result = await handler.execute("default", [pending])
        assert result.successes == []
        mock_repository.mark_sessions_terminating.assert_not_called()

    async def test_preemption_triggers_mark_terminating(
        self,
        handler: PreemptSessionsLifecycleHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """When a low-priority preemptible session blocks a high-priority pending session,
        it should be marked as TERMINATING."""
        now = datetime.now(tzutc())
        running_session = _make_running_session(
            priority=3,
            is_preemptible=True,
            cpu="2",
            mem="4096",
            created_at=now - timedelta(hours=1),
        )
        # Resources: total=8/16384, occupied=6/12288 → free=2/4096
        # Pending session needs 2 CPU / 4096 mem → exactly fits BUT for the deficit test we need shortage
        # Let's use more occupied: free = 0/0
        scheduling_data = _make_scheduling_data(
            total_cpu="4",
            total_mem="8192",
            occupied_cpu="4",
            occupied_mem="8192",  # fully occupied
        )
        mock_repository.get_scheduling_data.return_value = scheduling_data
        mock_repository.get_running_sessions_for_preemption.return_value = [running_session]

        # Create pending session with priority 10 (higher than running session's priority 3)
        pending = _create_session(status=SessionStatus.PENDING)
        # Set priority and requested_slots on the pending session
        pending.session_info.metadata.priority = 10
        pending.session_info.identity.priority = 10
        pending.session_info.resource.requested_slots = ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal("4096"),
        })

        await handler.execute("default", [pending])

        mock_repository.mark_sessions_terminating.assert_called_once_with(
            [running_session.session_id],
            reason="PREEMPTED",
        )

    async def test_no_preemption_when_no_preemptible_running_sessions(
        self,
        handler: PreemptSessionsLifecycleHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """No preemption when no preemptible running sessions exist."""
        scheduling_data = _make_scheduling_data(
            total_cpu="4",
            total_mem="8192",
            occupied_cpu="4",
            occupied_mem="8192",
        )
        mock_repository.get_scheduling_data.return_value = scheduling_data
        mock_repository.get_running_sessions_for_preemption.return_value = []

        pending = _create_session(status=SessionStatus.PENDING)
        pending.session_info.metadata.priority = 10
        pending.session_info.resource.requested_slots = ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal("4096"),
        })

        result = await handler.execute("default", [pending])
        assert result.successes == []
        mock_repository.mark_sessions_terminating.assert_not_called()
