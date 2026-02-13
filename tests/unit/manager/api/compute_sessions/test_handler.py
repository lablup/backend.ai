"""Tests for compute sessions REST API handler and adapter.

These tests focus on the adapter's conversion logic and the handler's
orchestration of session + kernel queries.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.dto.manager.compute_session import (
    ComputeSessionFilter,
    ComputeSessionOrder,
    ComputeSessionOrderField,
    OrderDirection,
    SearchComputeSessionsRequest,
)
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import (
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.api.compute_sessions.adapter import ComputeSessionsAdapter
from ai.backend.manager.data.kernel.types import (
    ClusterConfig,
    ImageInfo,
    KernelInfo,
    KernelStatus,
    LifecycleStatus,
    Metadata,
    Metrics,
    NetworkConfig,
    RelatedSessionInfo,
    ResourceInfo,
    RuntimeConfig,
    UserPermission,
)
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.repositories.base import NoPagination, OffsetPagination
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction

# ========== Test Data Factories ==========


def create_session_data(
    session_id: UUID | None = None,
    name: str = "test-session",
    status: SessionStatus = SessionStatus.RUNNING,
    scaling_group: str = "default",
    images: list[str] | None = None,
) -> SessionData:
    """Create a SessionData for testing."""
    return SessionData(
        id=session_id or uuid4(),
        session_type=SessionTypes.INTERACTIVE,
        priority=0,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        domain_name="default",
        group_id=uuid4(),
        user_uuid=uuid4(),
        occupying_slots=ResourceSlot({"cpu": Decimal("2.0"), "mem": Decimal("4294967296")}),
        requested_slots=ResourceSlot({"cpu": Decimal("4.0"), "mem": Decimal("8589934592")}),
        use_host_network=False,
        created_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
        status=status,
        result=SessionResult.UNDEFINED,
        num_queries=0,
        creation_id="test-creation-id",
        name=name,
        access_key=None,
        agent_ids=["agent-001"],
        images=images or ["cr.backend.ai/stable/python:3.11"],
        tag=None,
        vfolder_mounts=None,
        environ=None,
        bootstrap_script=None,
        target_sgroup_names=None,
        timeout=None,
        batch_timeout=None,
        terminated_at=None,
        scaling_group_name=scaling_group,
        starts_at=None,
        status_info=None,
        status_data=None,
        status_history=None,
        callback_url=None,
        startup_command=None,
        last_stat=None,
        network_type=None,
        network_id=None,
        owner=None,
        service_ports=None,
    )


def create_kernel_info(
    kernel_id: KernelId | None = None,
    session_id: str = "00000000-0000-0000-0000-000000000001",
    agent: str = "agent-001",
    status: KernelStatus = KernelStatus.RUNNING,
    last_stat: dict[str, Any] | None = None,
) -> KernelInfo:
    """Create a KernelInfo for testing."""
    return KernelInfo(
        id=kernel_id or KernelId(uuid4()),
        session=RelatedSessionInfo(
            session_id=session_id,
            creation_id="test-creation-id",
            name="test-session",
            session_type=SessionTypes.INTERACTIVE,
        ),
        user_permission=UserPermission(
            user_uuid=uuid4(),
            access_key="TESTKEY",
            domain_name="default",
            group_id=uuid4(),
            uid=None,
            main_gid=None,
            gids=None,
        ),
        image=ImageInfo(
            identifier=None,
            registry=None,
            tag=None,
            architecture=None,
        ),
        network=NetworkConfig(
            kernel_host=None,
            repl_in_port=0,
            repl_out_port=0,
            stdin_port=0,
            stdout_port=0,
            service_ports=None,
            preopen_ports=None,
            use_host_network=False,
        ),
        cluster=ClusterConfig(
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            cluster_role="main",
            cluster_idx=0,
            local_rank=0,
            cluster_hostname="main",
        ),
        resource=ResourceInfo(
            scaling_group="default",
            agent=agent,
            agent_addr=None,
            container_id=None,
            occupied_slots=ResourceSlot({"cpu": Decimal("2.0")}),
            requested_slots=ResourceSlot({"cpu": Decimal("4.0")}),
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
        lifecycle=LifecycleStatus(
            status=status,
            result=SessionResult.UNDEFINED,
            created_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
            terminated_at=None,
            starts_at=None,
            status_changed=None,
            status_info=None,
            status_data=None,
            status_history=None,
            last_seen=None,
            last_observed_at=None,
        ),
        metrics=Metrics(
            num_queries=0,
            last_stat=last_stat,
            container_log=None,
        ),
        metadata=Metadata(
            callback_url=None,
            internal_data=None,
        ),
    )


# ========== Adapter Tests ==========


class TestComputeSessionsAdapter:
    """Tests for ComputeSessionsAdapter conversion logic."""

    def setup_method(self) -> None:
        self.adapter = ComputeSessionsAdapter()

    def test_build_session_querier_defaults(self) -> None:
        """Build querier with default request should use default pagination."""
        request = SearchComputeSessionsRequest()
        querier = self.adapter.build_session_querier(request)

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 50
        assert querier.pagination.offset == 0
        assert querier.conditions == []
        assert querier.orders == []

    def test_build_session_querier_with_pagination(self) -> None:
        """Build querier with custom pagination."""
        request = SearchComputeSessionsRequest(limit=100, offset=50)
        querier = self.adapter.build_session_querier(request)

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 100
        assert querier.pagination.offset == 50

    def test_build_session_querier_with_status_filter(self) -> None:
        """Build querier with status filter should produce conditions."""
        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(status=["RUNNING", "PENDING"])
        )
        querier = self.adapter.build_session_querier(request)

        assert len(querier.conditions) == 1

    def test_build_session_querier_with_order(self) -> None:
        """Build querier with order should produce orders."""
        request = SearchComputeSessionsRequest(
            order=[
                ComputeSessionOrder(
                    field=ComputeSessionOrderField.CREATED_AT,
                    direction=OrderDirection.ASC,
                )
            ]
        )
        querier = self.adapter.build_session_querier(request)

        assert len(querier.orders) == 1

    def test_build_session_querier_with_name_filter(self) -> None:
        """Build querier with name filter should produce a condition."""
        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(name=StringFilter(contains="my-session"))
        )
        querier = self.adapter.build_session_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_session_querier_with_access_key_filter(self) -> None:
        """Build querier with access_key filter should produce a condition."""
        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(access_key=StringFilter(equals="TESTKEY"))
        )
        querier = self.adapter.build_session_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_session_querier_with_domain_name_filter(self) -> None:
        """Build querier with domain_name filter should produce a condition."""
        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(domain_name=StringFilter(starts_with="prod"))
        )
        querier = self.adapter.build_session_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_session_querier_with_scaling_group_filter(self) -> None:
        """Build querier with scaling_group_name filter should produce a condition."""
        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(scaling_group_name=StringFilter(equals="default"))
        )
        querier = self.adapter.build_session_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_session_querier_with_multiple_filters(self) -> None:
        """Build querier with multiple filter fields should produce multiple conditions."""
        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(
                status=["RUNNING"],
                name=StringFilter(contains="test"),
                access_key=StringFilter(equals="TESTKEY"),
                domain_name=StringFilter(i_contains="default"),
            )
        )
        querier = self.adapter.build_session_querier(request)

        # 1 status + 1 name + 1 access_key + 1 domain_name
        assert len(querier.conditions) == 4

    def test_build_session_querier_with_case_insensitive_name_filter(self) -> None:
        """Build querier with case-insensitive name filter should produce a condition."""
        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(name=StringFilter(i_equals="My-Session"))
        )
        querier = self.adapter.build_session_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_session_querier_with_negated_filter(self) -> None:
        """Build querier with negated filter should produce a condition."""
        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(name=StringFilter(not_contains="debug"))
        )
        querier = self.adapter.build_session_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_kernel_querier_for_sessions(self) -> None:
        """Build kernel querier should use NoPagination and session_id condition."""
        session_ids = [SessionId(uuid4()), SessionId(uuid4())]
        querier = self.adapter.build_kernel_querier_for_sessions(session_ids)

        assert isinstance(querier.pagination, NoPagination)
        assert len(querier.conditions) == 1
        assert querier.orders == []

    def test_group_kernels_by_session(self) -> None:
        """Group kernels by session should produce correct mapping."""
        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())

        kernels = [
            create_kernel_info(session_id=session_id_1),
            create_kernel_info(session_id=session_id_1),
            create_kernel_info(session_id=session_id_2),
        ]

        grouped = self.adapter.group_kernels_by_session(kernels)

        assert len(grouped[UUID(session_id_1)]) == 2
        assert len(grouped[UUID(session_id_2)]) == 1

    def test_convert_session_to_dto_without_containers(self) -> None:
        """Convert session without containers should have empty containers list."""
        session = create_session_data()
        dto = self.adapter.convert_session_to_dto(session, kernels=None)

        assert dto.id == session.id
        assert dto.name == session.name
        assert dto.type == SessionTypes.INTERACTIVE.value
        assert dto.status == SessionStatus.RUNNING.value
        assert dto.scaling_group == "default"
        assert dto.containers == []
        assert dto.resource_slots is not None
        assert dto.occupied_slots is not None

    def test_convert_session_to_dto_with_containers(self) -> None:
        """Convert session with containers should include all containers."""
        session_id = uuid4()
        session = create_session_data(session_id=session_id)
        kernels = [
            create_kernel_info(
                session_id=str(session_id),
                agent="agent-001",
                last_stat={"cpu_used": 100},
            ),
            create_kernel_info(
                session_id=str(session_id),
                agent="agent-002",
            ),
        ]
        dto = self.adapter.convert_session_to_dto(session, kernels=kernels)

        assert len(dto.containers) == 2
        assert dto.containers[0].agent_id == "agent-001"
        assert dto.containers[0].status == KernelStatus.RUNNING.value
        assert dto.containers[0].resource_usage == {"cpu_used": 100}
        assert dto.containers[1].agent_id == "agent-002"
        assert dto.containers[1].resource_usage is None

    def test_convert_session_to_dto_fields(self) -> None:
        """All required fields should be present in the DTO."""
        session = create_session_data(
            name="my-session",
            status=SessionStatus.TERMINATED,
        )
        session.terminated_at = datetime(2024, 6, 2, 12, 0, 0, tzinfo=UTC)
        session.starts_at = datetime(2024, 6, 1, 11, 0, 0, tzinfo=UTC)

        dto = self.adapter.convert_session_to_dto(session)

        assert dto.name == "my-session"
        assert dto.status == "TERMINATED"
        assert dto.terminated_at == datetime(2024, 6, 2, 12, 0, 0, tzinfo=UTC)
        assert dto.starts_at == datetime(2024, 6, 1, 11, 0, 0, tzinfo=UTC)
        assert dto.image == ["cr.backend.ai/stable/python:3.11"]

    def test_convert_session_to_dto_mixed_statuses(self) -> None:
        """All session statuses should be represented correctly."""
        for status in [
            SessionStatus.PENDING,
            SessionStatus.RUNNING,
            SessionStatus.TERMINATED,
            SessionStatus.ERROR,
            SessionStatus.CANCELLED,
        ]:
            session = create_session_data(status=status)
            dto = self.adapter.convert_session_to_dto(session)
            assert dto.status == status.value


# ========== Handler Orchestration Tests ==========


class TestComputeSessionsHandler:
    """Tests for handler orchestration logic with mocked processors."""

    @pytest.fixture
    def mock_session_result_empty(self) -> MagicMock:
        """Mock session search result with no sessions."""
        result = MagicMock()
        result.data = []
        result.total_count = 0
        result.has_next_page = False
        result.has_previous_page = False
        return result

    @pytest.fixture
    def mock_session_result_with_data(self) -> MagicMock:
        """Mock session search result with sessions."""
        session_1 = create_session_data(
            session_id=UUID("11111111-1111-1111-1111-111111111111"),
            name="session-1",
        )
        session_2 = create_session_data(
            session_id=UUID("22222222-2222-2222-2222-222222222222"),
            name="session-2",
        )
        result = MagicMock()
        result.data = [session_1, session_2]
        result.total_count = 2
        result.has_next_page = False
        result.has_previous_page = False
        return result

    @pytest.fixture
    def mock_kernel_result_for_sessions(self) -> MagicMock:
        """Mock kernel search result for the sessions above."""
        kernels = [
            create_kernel_info(
                session_id="11111111-1111-1111-1111-111111111111",
                agent="agent-001",
            ),
            create_kernel_info(
                session_id="11111111-1111-1111-1111-111111111111",
                agent="agent-002",
            ),
            create_kernel_info(
                session_id="22222222-2222-2222-2222-222222222222",
                agent="agent-003",
            ),
        ]
        result = MagicMock()
        result.data = kernels
        result.total_count = 3
        result.has_next_page = False
        result.has_previous_page = False
        return result

    @pytest.fixture
    def mock_processors(
        self,
        mock_session_result_with_data: MagicMock,
        mock_kernel_result_for_sessions: MagicMock,
    ) -> MagicMock:
        """Mock processors for session + kernel queries."""
        processors = MagicMock()
        processors.session.search_sessions.wait_for_complete = AsyncMock(
            return_value=mock_session_result_with_data
        )
        processors.session.search_kernels.wait_for_complete = AsyncMock(
            return_value=mock_kernel_result_for_sessions
        )
        return processors

    @pytest.mark.asyncio
    async def test_search_sessions_calls_both_processors(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Handler should call both search_sessions and search_kernels."""
        await mock_processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=MagicMock())
        )
        mock_processors.session.search_sessions.wait_for_complete.assert_called_once()

        await mock_processors.session.search_kernels.wait_for_complete(
            SearchKernelsAction(querier=MagicMock())
        )
        mock_processors.session.search_kernels.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_sessions_empty_result(
        self,
        mock_session_result_empty: MagicMock,
    ) -> None:
        """Handler with empty result should not query kernels."""
        processors = MagicMock()
        processors.session.search_sessions.wait_for_complete = AsyncMock(
            return_value=mock_session_result_empty
        )

        result = await processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=MagicMock())
        )

        assert result.data == []
        assert result.total_count == 0
        # search_kernels should not be called for empty sessions
        processors.session.search_kernels.wait_for_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_result_has_correct_container_grouping(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Kernels should be correctly grouped by session ID."""
        session_result = await mock_processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=MagicMock())
        )
        kernel_result = await mock_processors.session.search_kernels.wait_for_complete(
            SearchKernelsAction(querier=MagicMock())
        )

        adapter = ComputeSessionsAdapter()
        kernels_by_session = adapter.group_kernels_by_session(kernel_result.data)

        # session-1 should have 2 kernels, session-2 should have 1
        items = [
            adapter.convert_session_to_dto(session, kernels_by_session.get(session.id, []))
            for session in session_result.data
        ]

        assert len(items) == 2
        assert len(items[0].containers) == 2
        assert len(items[1].containers) == 1

    @pytest.mark.asyncio
    async def test_pagination_info_is_correct(
        self,
        mock_processors: MagicMock,
    ) -> None:
        """Pagination info should reflect the session search result."""
        session_result = await mock_processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=MagicMock())
        )

        assert session_result.total_count == 2

    @pytest.mark.asyncio
    async def test_multiple_containers_per_session(self) -> None:
        """Session with multiple containers should have all of them."""
        session_id = uuid4()
        session = create_session_data(session_id=session_id)
        kernels = [
            create_kernel_info(session_id=str(session_id), agent=f"agent-{i:03d}") for i in range(5)
        ]

        adapter = ComputeSessionsAdapter()
        dto = adapter.convert_session_to_dto(session, kernels=kernels)

        assert len(dto.containers) == 5
        agents = {c.agent_id for c in dto.containers}
        assert len(agents) == 5

    @pytest.mark.asyncio
    async def test_session_with_no_containers(self) -> None:
        """Session with no containers should have empty containers array."""
        session = create_session_data()

        adapter = ComputeSessionsAdapter()
        dto = adapter.convert_session_to_dto(session, kernels=[])

        assert dto.containers == []
