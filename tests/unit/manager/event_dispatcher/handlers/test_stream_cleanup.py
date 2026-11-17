from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.events.event_types.kernel.broadcast import (
    KernelTerminatingBroadcastEvent,
)
from ai.backend.common.types import (
    AgentId,
    ClusterMode,
    KernelId,
    SessionId,
    SessionResult,
    SessionTypes,
)
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
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.event_dispatcher.handlers.stream_cleanup import (
    StreamCleanupEventHandler,
)
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository

_KERNEL_ID = KernelId(UUID("00000000-0000-0000-0000-0000000000a1"))
_SESSION_ID = SessionId(UUID("00000000-0000-0000-0000-0000000000b1"))
_EVENT = KernelTerminatingBroadcastEvent(kernel_id=_KERNEL_ID, session_id=_SESSION_ID)


def _make_kernel_info(cluster_role: str) -> KernelInfo:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    return KernelInfo(
        id=_KERNEL_ID,
        session=RelatedSessionInfo(
            session_id=str(_SESSION_ID),
            creation_id="creation",
            name="session",
            session_type=SessionTypes.INTERACTIVE,
        ),
        user_permission=UserPermission(
            user_uuid=UUID("00000000-0000-0000-0000-0000000000c1"),
            access_key="access-key",
            domain_name="default",
            group_id=UUID("00000000-0000-0000-0000-0000000000d1"),
            uid=None,
            main_gid=None,
            gids=None,
        ),
        image=ImageInfo(
            image_id=None,
            identifier=None,
            registry=None,
            tag=None,
            architecture=None,
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
            cluster_role=cluster_role,
            cluster_idx=0,
            local_rank=0,
            cluster_hostname="kernel-0",
        ),
        resource=ResourceInfo(
            resource_group="default",
            resource_group_id=ResourceGroupID(UUID("00000000-0000-0000-0000-0000000000e1")),
            agent=AgentId("i-agent"),
            agent_addr="tcp://i-agent:6001",
            container_id="container",
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
            status=KernelStatus.TERMINATING,
            result=SessionResult.UNDEFINED,
            created_at=created_at,
            terminated_at=None,
            starts_at=None,
            status_changed=created_at,
            status_info=None,
            status_data=None,
            status_history=None,
            last_seen=None,
            last_observed_at=None,
        ),
        metrics=Metrics(num_queries=0, last_stat=None, container_log=None),
        metadata=Metadata(callback_url=None, internal_data=None),
        kernel_group_id=None,
    )


def _make_result(items: list[KernelInfo]) -> KernelListResult:
    return KernelListResult(
        items=items,
        total_count=len(items),
        has_next_page=False,
        has_previous_page=False,
    )


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=SchedulerRepository)


@pytest.fixture
def callback() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def handler(repository: AsyncMock, callback: AsyncMock) -> StreamCleanupEventHandler:
    handler = StreamCleanupEventHandler(repository)
    handler.register_cleanup_callback(callback)
    return handler


class TestHandleKernelTerminatingBroadcast:
    async def test_main_kernel_runs_the_callbacks(
        self,
        handler: StreamCleanupEventHandler,
        repository: AsyncMock,
        callback: AsyncMock,
    ) -> None:
        kernel = _make_kernel_info(DEFAULT_ROLE)
        repository.search_kernels_for_handler.return_value = _make_result([kernel])

        await handler.handle_kernel_terminating_broadcast(None, AgentId("i-agent"), _EVENT)

        callback.assert_awaited_once_with(kernel)

    async def test_reads_only_the_kernel_of_the_event(
        self,
        handler: StreamCleanupEventHandler,
        repository: AsyncMock,
    ) -> None:
        repository.search_kernels_for_handler.return_value = _make_result([])

        await handler.handle_kernel_terminating_broadcast(None, AgentId("i-agent"), _EVENT)

        searcher = repository.search_kernels_for_handler.await_args.args[0]
        conditions = [condition() for condition in searcher.conditions]
        assert len(conditions) == 1
        assert conditions[0].compare(KernelRow.id == _KERNEL_ID)

    async def test_failing_callback_does_not_stop_the_others(
        self,
        handler: StreamCleanupEventHandler,
        repository: AsyncMock,
        callback: AsyncMock,
    ) -> None:
        failing_callback = AsyncMock(side_effect=RuntimeError("cleanup failed"))
        handler.register_cleanup_callback(failing_callback)
        kernel = _make_kernel_info(DEFAULT_ROLE)
        repository.search_kernels_for_handler.return_value = _make_result([kernel])

        await handler.handle_kernel_terminating_broadcast(None, AgentId("i-agent"), _EVENT)

        failing_callback.assert_awaited_once_with(kernel)
        callback.assert_awaited_once_with(kernel)

    async def test_sub_kernel_skips_the_callbacks(
        self,
        handler: StreamCleanupEventHandler,
        repository: AsyncMock,
        callback: AsyncMock,
    ) -> None:
        repository.search_kernels_for_handler.return_value = _make_result([
            _make_kernel_info("sub")
        ])

        await handler.handle_kernel_terminating_broadcast(None, AgentId("i-agent"), _EVENT)

        callback.assert_not_awaited()

    async def test_missing_kernel_skips_the_callbacks(
        self,
        handler: StreamCleanupEventHandler,
        repository: AsyncMock,
        callback: AsyncMock,
    ) -> None:
        repository.search_kernels_for_handler.return_value = _make_result([])

        await handler.handle_kernel_terminating_broadcast(None, AgentId("i-agent"), _EVENT)

        callback.assert_not_awaited()
