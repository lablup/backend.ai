"""Unit tests for v2 SessionAdapter."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.v2.common import (
    ResourceSlotEntryInfo,
    ResourceSlotEntryInput,
    ResourceSlotInfo,
)
from ai.backend.common.dto.manager.v2.kernel.response import ResourceAllocationGQLDTO
from ai.backend.common.dto.manager.v2.session.request import (
    BatchConfigInput,
    EnqueueSessionInput,
    TerminateSessionsInput,
)
from ai.backend.common.dto.manager.v2.session.types import (
    ClusterModeEnum,
    CreateSessionTypeEnum,
)
from ai.backend.common.dto.manager.v2.session_options.types import AgentSelectionPolicyEnum
from ai.backend.common.types import ClusterMode, SessionResult, SessionTypes
from ai.backend.manager.actions.v2.bulk.result import (
    PartialBulkEntityResult,
    PartialBulkResult,
)
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.data.session.types import (
    SessionData,
    SessionStatus,
    SessionTerminationStatus,
)
from ai.backend.manager.services.session.actions.batch_get_session_resource_allocation import (
    BatchGetSessionResourceAllocationAction,
)


def _create_session_data(
    session_id: UUID | None = None,
    name: str = "test-session",
    status: SessionStatus = SessionStatus.PENDING,
) -> SessionData:
    """Create a minimal SessionData for testing adapter conversion."""
    return SessionData(
        id=session_id or uuid4(),
        session_type=SessionTypes.INTERACTIVE,
        priority=10,
        job_priority=0,
        is_preemptible=True,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        domain_name="default",
        group_id=uuid4(),
        user_uuid=uuid4(),
        use_host_network=False,
        created_at=datetime.now(tz=UTC),
        status=status,
        result=SessionResult.UNDEFINED,
        num_queries=0,
        creation_id="test-creation-id",
        name=name,
        access_key=None,
        resource_group_name="default",
        target_sgroup_names=None,
        agent_ids=None,
        images=None,
        image_ids=None,
        tag=None,
        terminated_at=None,
        starts_at=None,
        batch_timeout=None,
        status_info=None,
        status_data=None,
        status_history=None,
        vfolder_mounts=None,
        environ=None,
        bootstrap_script=None,
        startup_command=None,
        callback_url=None,
        timeout=None,
        last_stat=None,
        owner=None,
        network_type=None,
        network_id=None,
        service_ports=None,
    )


def _create_allocation(
    requested: dict[str, Decimal] | None = None,
    used: dict[str, Decimal] | None = None,
) -> ResourceAllocationGQLDTO:
    """Build the slot allocation the adapter receives from resource_allocations."""

    def _entries(slots: dict[str, Decimal] | None) -> ResourceSlotInfo:
        return ResourceSlotInfo(
            entries=[
                ResourceSlotEntryInfo(resource_type=k, quantity=v) for k, v in (slots or {}).items()
            ]
        )

    return ResourceAllocationGQLDTO(
        requested=_entries(requested),
        used=_entries(used),
        allocated=_entries(used),
    )


class TestSessionDataToNode:
    """Tests for _session_data_to_node conversion."""

    def test_basic_conversion(self) -> None:
        """SessionData should convert to SessionNode with correct fields."""
        data = _create_session_data(name="my-session")
        node = SessionAdapter._session_data_to_node(data, _create_allocation())

        assert node.metadata.name == "my-session"
        assert node.metadata.session_type == "interactive"
        assert node.metadata.cluster_mode == "SINGLE_NODE"
        assert node.metadata.cluster_size == 1
        assert node.metadata.priority == 10

    def test_resource_allocation_conversion(self) -> None:
        """Resource slots should be converted to ResourceSlotInfo entries."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(
            data,
            _create_allocation(
                requested={"cpu": Decimal("1"), "mem": Decimal("1073741824")},
            ),
        )

        requested = node.resource.allocation.requested
        assert len(requested.entries) == 2
        types = {e.resource_type for e in requested.entries}
        assert "cpu" in types
        assert "mem" in types

    def test_lifecycle_running_status(self) -> None:
        """RUNNING status should be preserved as RUNNING."""
        data = _create_session_data(status=SessionStatus.RUNNING)
        node = SessionAdapter._session_data_to_node(data, _create_allocation())
        assert node.lifecycle.status == "RUNNING"

    def test_lifecycle_pending_status(self) -> None:
        """PENDING status should be preserved as PENDING."""
        data = _create_session_data(status=SessionStatus.PENDING)
        node = SessionAdapter._session_data_to_node(data, _create_allocation())
        assert node.lifecycle.status == "PENDING"

    def test_lifecycle_result(self) -> None:
        """Result should be passed through as string value."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data, _create_allocation())
        assert node.lifecycle.result == "undefined"

    def test_domain_and_user_fields(self) -> None:
        """Domain name and user/project IDs should be mapped."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data, _create_allocation())
        assert node.domain_name == "default"
        assert node.user_id == data.user_uuid
        assert node.project_id == data.group_id

    def test_network_host_network_false(self) -> None:
        """Network info should reflect use_host_network."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data, _create_allocation())
        assert node.network.use_host_network is False

    def test_empty_occupying_slots(self) -> None:
        """Empty occupying slots should produce empty entries list."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data, _create_allocation())
        assert len(node.resource.allocation.used.entries) == 0


async def _no_allocations(
    action: BatchGetSessionResourceAllocationAction,
) -> PartialBulkResult[ResourceAllocationAggregate]:
    """The read answers for every session named, each holding nothing."""
    return PartialBulkResult(
        items=[
            PartialBulkEntityResult[ResourceAllocationAggregate].nothing(SessionID(sid))
            for sid in action.session_ids
        ]
    )


class TestEnqueueActionBuilding:
    """Tests for adapter.enqueue() action construction."""

    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        processors = MagicMock()
        result = MagicMock()
        result.session_data = _create_session_data()
        processors.session.enqueue_session.run = AsyncMock(return_value=result)
        processors.session.batch_get_session_resource_allocation.run = AsyncMock(
            side_effect=_no_allocations
        )
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> SessionAdapter:
        return SessionAdapter(mock_processors)

    async def test_enqueue_interactive(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """Enqueue interactive session should create correct action."""
        user_id = uuid4()
        project_id = uuid4()
        dto = EnqueueSessionInput(
            session_name="test-session",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid4(),
            resource_entries=[
                ResourceSlotEntryInput(resource_type="cpu", quantity="1"),
                ResourceSlotEntryInput(resource_type="mem", quantity="1g"),
            ],
            project_id=project_id,
        )
        result = await adapter.enqueue(
            dto,
            user_id=user_id,
            user_role="user",
            access_key="TESTKEY",
            domain_name="default",
            group_id=project_id,
        )
        assert result.session is not None
        mock_processors.session.enqueue_session.run.assert_called_once()
        action = mock_processors.session.enqueue_session.run.call_args[0][0]
        assert action.session_type == SessionTypes.INTERACTIVE
        assert action.resource.cluster_mode == ClusterMode.SINGLE_NODE

    async def test_enqueue_batch_with_config(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """Enqueue batch session should include batch spec."""
        dto = EnqueueSessionInput(
            session_name="batch-job",
            session_type=CreateSessionTypeEnum.BATCH,
            image_id=uuid4(),
            resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="2")],
            project_id=uuid4(),
            batch=BatchConfigInput(startup_command="python train.py", batch_timeout=3600),
        )
        await adapter.enqueue(
            dto,
            user_id=uuid4(),
            user_role="user",
            access_key="TESTKEY",
            domain_name="default",
            group_id=dto.project_id,
        )
        action = mock_processors.session.enqueue_session.run.call_args[0][0]
        assert action.session_type == SessionTypes.BATCH
        assert action.batch is not None
        assert action.batch.startup_command == "python train.py"

    async def test_enqueue_multi_node_cluster(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """Enqueue with multi-node cluster mode should be reflected in the action."""
        dto = EnqueueSessionInput(
            session_name="cluster-session",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid4(),
            resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
            project_id=uuid4(),
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            cluster_size=4,
        )
        await adapter.enqueue(
            dto,
            user_id=uuid4(),
            user_role="user",
            access_key="TESTKEY",
            domain_name="default",
            group_id=dto.project_id,
        )
        action = mock_processors.session.enqueue_session.run.call_args[0][0]
        assert action.resource.cluster_mode == ClusterMode.MULTI_NODE
        assert action.resource.cluster_size == 4

    async def test_enqueue_with_agent_selection_policy(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """A request-level policy should be converted to the domain enum."""
        dto = EnqueueSessionInput(
            session_name="strict-session",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid4(),
            resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
            project_id=uuid4(),
            agent_list=["agent-1"],
            agent_selection_policy=AgentSelectionPolicyEnum.STRICT,
        )
        await adapter.enqueue(
            dto,
            user_id=uuid4(),
            user_role="user",
            access_key="TESTKEY",
            domain_name="default",
            group_id=dto.project_id,
        )
        action = mock_processors.session.enqueue_session.run.call_args[0][0]
        assert action.scheduling.agent_list == ["agent-1"]
        assert action.scheduling.agent_selection_policy == AgentSelectionPolicy.STRICT

    async def test_enqueue_without_agent_selection_policy(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """An omitted policy should stay None so the RG default applies."""
        dto = EnqueueSessionInput(
            session_name="default-policy-session",
            session_type=CreateSessionTypeEnum.INTERACTIVE,
            image_id=uuid4(),
            resource_entries=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
            project_id=uuid4(),
        )
        await adapter.enqueue(
            dto,
            user_id=uuid4(),
            user_role="user",
            access_key="TESTKEY",
            domain_name="default",
            group_id=dto.project_id,
        )
        action = mock_processors.session.enqueue_session.run.call_args[0][0]
        assert action.scheduling.agent_selection_policy is None


class TestTerminateActionBuilding:
    """Tests for adapter.terminate() action construction."""

    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        processors = MagicMock()
        result = PartialBulkResult(
            items=[
                PartialBulkEntityResult[SessionTerminationStatus].succeeded(
                    SessionID(uuid4()), SessionTerminationStatus.TERMINATING
                )
            ]
        )
        processors.session.terminate_sessions.run = AsyncMock(return_value=result)
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> SessionAdapter:
        return SessionAdapter(mock_processors)

    async def test_terminate_single(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """Terminate single session."""
        sid = uuid4()
        dto = TerminateSessionsInput(session_ids=[sid])
        result = await adapter.terminate(dto)
        assert len(result.terminating) == 1
        mock_processors.session.terminate_sessions.run.assert_called_once()

    async def test_terminate_forced(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """Force terminate should pass forced=True to action."""
        dto = TerminateSessionsInput(session_ids=[uuid4()], forced=True)
        await adapter.terminate(dto)
        action = mock_processors.session.terminate_sessions.run.call_args[0][0]
        assert action.forced is True

    async def test_terminate_multiple(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """Terminate multiple sessions should pass all IDs."""
        ids = [uuid4(), uuid4(), uuid4()]
        dto = TerminateSessionsInput(session_ids=ids)
        await adapter.terminate(dto)
        action = mock_processors.session.terminate_sessions.run.call_args[0][0]
        assert len(action.session_ids) == 3
