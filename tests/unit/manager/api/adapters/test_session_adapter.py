"""Unit tests for v2 SessionAdapter."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.session.request import (
    BatchConfigInput,
    EnqueueSessionInput,
    TerminateSessionsInput,
)
from ai.backend.common.dto.manager.v2.session.types import (
    ClusterModeEnum,
    CreateSessionTypeEnum,
)
from ai.backend.common.types import ClusterMode, SessionResult, SessionTypes
from ai.backend.manager.api.adapters.session import SessionAdapter
from ai.backend.manager.data.session.types import SessionData, SessionStatus


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
        is_preemptible=True,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        domain_name="default",
        group_id=uuid4(),
        user_uuid=uuid4(),
        occupying_slots={},
        requested_slots={"cpu": Decimal("1"), "mem": Decimal("1073741824")},
        use_host_network=False,
        created_at=datetime.now(tz=UTC),
        status=status,
        result=SessionResult.UNDEFINED,
        num_queries=0,
        creation_id="test-creation-id",
        name=name,
        access_key=None,
        scaling_group_name="default",
        target_sgroup_names=None,
        agent_ids=None,
        images=None,
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


class TestSessionDataToNode:
    """Tests for _session_data_to_node conversion."""

    def test_basic_conversion(self) -> None:
        """SessionData should convert to SessionNode with correct fields."""
        data = _create_session_data(name="my-session")
        node = SessionAdapter._session_data_to_node(data)

        assert node.metadata.name == "my-session"
        assert node.metadata.session_type == "interactive"
        assert node.metadata.cluster_mode == "SINGLE_NODE"
        assert node.metadata.cluster_size == 1
        assert node.metadata.priority == 10

    def test_resource_allocation_conversion(self) -> None:
        """Resource slots should be converted to ResourceSlotInfo entries."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data)

        requested = node.resource.allocation.requested
        assert len(requested.entries) == 2
        types = {e.resource_type for e in requested.entries}
        assert "cpu" in types
        assert "mem" in types

    def test_lifecycle_running_status(self) -> None:
        """RUNNING status should be preserved as RUNNING."""
        data = _create_session_data(status=SessionStatus.RUNNING)
        node = SessionAdapter._session_data_to_node(data)
        assert node.lifecycle.status == "RUNNING"

    def test_lifecycle_pending_status(self) -> None:
        """PENDING status should be preserved as PENDING."""
        data = _create_session_data(status=SessionStatus.PENDING)
        node = SessionAdapter._session_data_to_node(data)
        assert node.lifecycle.status == "PENDING"

    def test_lifecycle_result(self) -> None:
        """Result should be passed through as string value."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data)
        assert node.lifecycle.result == "undefined"

    def test_domain_and_user_fields(self) -> None:
        """Domain name and user/project IDs should be mapped."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data)
        assert node.domain_name == "default"
        assert node.user_id == data.user_uuid
        assert node.project_id == data.group_id

    def test_network_host_network_false(self) -> None:
        """Network info should reflect use_host_network."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data)
        assert node.network.use_host_network is False

    def test_empty_occupying_slots(self) -> None:
        """Empty occupying slots should produce empty entries list."""
        data = _create_session_data()
        node = SessionAdapter._session_data_to_node(data)
        assert len(node.resource.allocation.used.entries) == 0


class TestEnqueueActionBuilding:
    """Tests for adapter.enqueue() action construction."""

    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        processors = MagicMock()
        result = MagicMock()
        result.session_data = _create_session_data()
        processors.session.enqueue_session.wait_for_complete = AsyncMock(return_value=result)
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
        mock_processors.session.enqueue_session.wait_for_complete.assert_called_once()
        action = mock_processors.session.enqueue_session.wait_for_complete.call_args[0][0]
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
        action = mock_processors.session.enqueue_session.wait_for_complete.call_args[0][0]
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
        action = mock_processors.session.enqueue_session.wait_for_complete.call_args[0][0]
        assert action.resource.cluster_mode == ClusterMode.MULTI_NODE
        assert action.resource.cluster_size == 4


class TestTerminateActionBuilding:
    """Tests for adapter.terminate() action construction."""

    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        processors = MagicMock()
        result = MagicMock()
        result.cancelled = []
        result.terminating = [uuid4()]
        result.force_terminated = []
        result.skipped = []
        processors.session.terminate_sessions.wait_for_complete = AsyncMock(return_value=result)
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
        mock_processors.session.terminate_sessions.wait_for_complete.assert_called_once()

    async def test_terminate_forced(
        self,
        adapter: SessionAdapter,
        mock_processors: MagicMock,
    ) -> None:
        """Force terminate should pass forced=True to action."""
        dto = TerminateSessionsInput(session_ids=[uuid4()], forced=True)
        await adapter.terminate(dto)
        action = mock_processors.session.terminate_sessions.wait_for_complete.call_args[0][0]
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
        action = mock_processors.session.terminate_sessions.wait_for_complete.call_args[0][0]
        assert len(action.session_ids) == 3
