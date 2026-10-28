from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import CREATION_DESTROYED_MESSAGE, KernelOwnershipData, LifecycleEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import AgentId, ContainerId, KernelId, SessionId

CONTAINER_ID = ContainerId("c0ffee")


@pytest.fixture
def ownership_data() -> KernelOwnershipData:
    return KernelOwnershipData(
        kernel_id=KernelId(uuid.uuid4()),
        session_id=SessionId(uuid.uuid4()),
        agent_id=AgentId("i-test"),
    )


@pytest.fixture
def kernel_config() -> dict[str, Any]:
    return {
        "environ": {},
        "image": {"labels": {}, "digest": "sha256:0", "registry": {}},
        "mounts": [],
        "session_type": "interactive",
        "cluster_role": "main",
        "resource_opts": {},
        "preopen_ports": [],
        "allocated_host_ports": [],
    }


@pytest.fixture
def kernel_obj() -> MagicMock:
    return MagicMock()


@pytest.fixture
def kernel_context(
    ownership_data: KernelOwnershipData, kernel_config: dict[str, Any], kernel_obj: MagicMock
) -> MagicMock:
    resource_spec = MagicMock(allocations={"cpu": {"cpu": []}}, mounts=[])
    ctx = MagicMock()
    ctx.kernel_id = ownership_data.kernel_id
    ctx.kernel_config = kernel_config
    ctx.kernel_features = frozenset()
    ctx.image_ref.architecture = "x86_64"
    ctx.image_ref.is_local = True
    ctx.get_overriding_uid.return_value = None
    ctx.get_overriding_gid.return_value = None
    ctx.get_supplementary_gids.return_value = []
    ctx.get_intrinsic_mounts = AsyncMock(return_value=[])
    ctx.get_extra_envs = AsyncMock(return_value={})
    ctx.generate_resource_spec = AsyncMock(return_value=(resource_spec, {}))
    ctx.prepare_container = AsyncMock(return_value=kernel_obj)
    ctx.start_container = AsyncMock(return_value={"container_id": CONTAINER_ID})
    for name in (
        "apply_network",
        "prepare_ssh",
        "inject_additional_device_env_vars",
        "process_mounts",
        "prepare_scratch",
        "mount_vfolders",
        "mount_krunner",
    ):
        setattr(ctx, name, AsyncMock())
    return ctx


@pytest.fixture
def agent(kernel_context: MagicMock) -> MagicMock:
    @contextmanager
    def track_create(*_args: object, **_kwargs: object) -> Iterator[bool]:
        yield True

    cpu = SimpleNamespace(instance=SimpleNamespace(get_attached_devices=AsyncMock(return_value=[])))
    agent = MagicMock()
    agent.failure_reporting_kernels = set()
    agent._active_creates = {}
    agent.kernel_registry = {}
    agent.track_create = track_create
    agent.registry_lock = AsyncMock()
    agent.resource_lock = AsyncMock()
    agent.local_config.resource.allocation_order = []
    agent.local_config.debug.log_kernel_config = False
    agent.local_config.debug.kernel_runner = False
    agent.local_config.container.sandbox_type = "docker"
    agent.local_config.container.jail_args = []
    agent.computers = {"cpu": cpu}
    agent.init_kernel_context = AsyncMock(return_value=kernel_context)
    for name in (
        "anycast_and_broadcast_event",
        "restart_kernel__store_config",
        "inject_container_lifecycle_event",
        "reconstruct_resource_usage",
    ):
        setattr(agent, name, AsyncMock())
    return agent


class TestCreateKernelInitFailure:
    @pytest.mark.parametrize("restarting", [False, True], ids=["new", "restarting"])
    @pytest.mark.parametrize(
        "error",
        [RuntimeError("kernel init failed"), asyncio.CancelledError()],
        ids=["init-error", "init-cancelled"],
    )
    async def test_init_failure_injects_failed_to_start_once(
        self,
        agent: MagicMock,
        kernel_obj: MagicMock,
        ownership_data: KernelOwnershipData,
        kernel_config: dict[str, Any],
        error: BaseException,
        restarting: bool,
    ) -> None:
        kernel_obj.init = AsyncMock(side_effect=error)

        with (
            patch("ai.backend.agent.agent.get_arch_name", return_value="x86_64"),
            patch("ai.backend.agent.agent.allocate"),
            pytest.raises(type(error)) as exc_info,
        ):
            await AbstractAgent.create_kernel(
                agent,
                ownership_data,
                MagicMock(),
                cast(Any, kernel_config),
                cast(Any, {}),
                restarting=restarting,
            )

        assert exc_info.value is error
        kernel_obj.init.assert_awaited_once()
        assert (ownership_data.kernel_id in agent.failure_reporting_kernels) is (not restarting)
        agent.inject_container_lifecycle_event.assert_awaited_once_with(
            ownership_data.kernel_id,
            ownership_data.session_id,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.FAILED_TO_START,
            container_id=CONTAINER_ID,
        )

    async def test_init_cancelled_by_a_destroy_does_not_inject_failed_to_start(
        self,
        agent: MagicMock,
        kernel_obj: MagicMock,
        ownership_data: KernelOwnershipData,
        kernel_config: dict[str, Any],
    ) -> None:
        """The destroy that cancelled the creation reports the termination itself."""
        error = asyncio.CancelledError(CREATION_DESTROYED_MESSAGE)
        kernel_obj.init = AsyncMock(side_effect=error)
        agent._active_creates = {
            ownership_data.kernel_id: SimpleNamespace(cancelled_by_destroy=True)
        }

        with (
            patch("ai.backend.agent.agent.get_arch_name", return_value="x86_64"),
            patch("ai.backend.agent.agent.allocate"),
            pytest.raises(asyncio.CancelledError) as exc_info,
        ):
            await AbstractAgent.create_kernel(
                agent,
                ownership_data,
                MagicMock(),
                cast(Any, kernel_config),
                cast(Any, {}),
            )

        assert exc_info.value is error
        kernel_obj.init.assert_awaited_once()
        agent.inject_container_lifecycle_event.assert_not_awaited()
