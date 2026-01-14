"""
Tests for KernelService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import KernelId, ResourceSlot, SessionResult, SessionTypes
from ai.backend.manager.data.kernel.types import (
    ClusterConfig,
    ImageInfo,
    KernelInfo,
    KernelListResult,
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
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.kernel import KernelRepository
from ai.backend.manager.services.kernel.actions.search import SearchKernelsAction
from ai.backend.manager.services.kernel.service import KernelService


class TestKernelService:
    """Test cases for KernelService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked KernelRepository"""
        return MagicMock(spec=KernelRepository)

    @pytest.fixture
    def kernel_service(self, mock_repository: MagicMock) -> KernelService:
        """Create KernelService instance with mocked repository"""
        return KernelService(repository=mock_repository)

    @pytest.fixture
    def sample_kernel_info(self) -> KernelInfo:
        """Create sample kernel info data"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        group_id = uuid.uuid4()

        return KernelInfo(
            id=kernel_id,
            session=RelatedSessionInfo(
                session_id=str(session_id),
                creation_id="test-creation-id",
                name="test-session",
                session_type=SessionTypes.INTERACTIVE,
            ),
            user_permission=UserPermission(
                user_uuid=user_id,
                access_key="TESTKEY",
                domain_name="default",
                group_id=group_id,
                uid=1000,
                main_gid=1000,
                gids=[1000],
            ),
            image=ImageInfo(
                identifier=None,
                registry="cr.backend.ai",
                tag="latest",
                architecture="x86_64",
            ),
            network=NetworkConfig(
                kernel_host="localhost",
                repl_in_port=2000,
                repl_out_port=2001,
                stdin_port=2002,
                stdout_port=2003,
                service_ports=None,
                preopen_ports=None,
                use_host_network=False,
            ),
            cluster=ClusterConfig(
                cluster_mode="single-node",
                cluster_size=1,
                cluster_role="main",
                cluster_idx=0,
                local_rank=0,
                cluster_hostname="main",
            ),
            resource=ResourceInfo(
                scaling_group="default",
                agent="test-agent",
                agent_addr="localhost:6001",
                container_id="container-123",
                occupied_slots=ResourceSlot({"cpu": "1", "mem": "1G"}),
                requested_slots=ResourceSlot({"cpu": "1", "mem": "1G"}),
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
                status=KernelStatus.RUNNING,
                result=SessionResult.UNDEFINED,
                created_at=datetime.now(tz=UTC),
                terminated_at=None,
                starts_at=None,
                status_changed=datetime.now(tz=UTC),
                status_info=None,
                status_data=None,
                status_history=None,
                last_seen=datetime.now(tz=UTC),
            ),
            metrics=Metrics(
                num_queries=0,
                last_stat=None,
                container_log=None,
            ),
            metadata=Metadata(
                callback_url=None,
                internal_data=None,
            ),
        )

    # =========================================================================
    # Tests - Search
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_kernels(
        self,
        kernel_service: KernelService,
        mock_repository: MagicMock,
        sample_kernel_info: KernelInfo,
    ) -> None:
        """Test searching kernels with querier"""
        mock_repository.search = AsyncMock(
            return_value=KernelListResult(
                items=[sample_kernel_info],
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
        action = SearchKernelsAction(querier=querier)
        result = await kernel_service.search(action)

        assert result.data == [sample_kernel_info]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier)

    @pytest.mark.asyncio
    async def test_search_kernels_empty_result(
        self,
        kernel_service: KernelService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching kernels when no results are found"""
        mock_repository.search = AsyncMock(
            return_value=KernelListResult(
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
        action = SearchKernelsAction(querier=querier)
        result = await kernel_service.search(action)

        assert result.data == []
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_search_kernels_with_pagination(
        self,
        kernel_service: KernelService,
        mock_repository: MagicMock,
        sample_kernel_info: KernelInfo,
    ) -> None:
        """Test searching kernels with pagination"""
        mock_repository.search = AsyncMock(
            return_value=KernelListResult(
                items=[sample_kernel_info],
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
        action = SearchKernelsAction(querier=querier)
        result = await kernel_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
