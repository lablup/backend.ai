from __future__ import annotations

import asyncio
import functools
import uuid
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors.agent import ContainerCreationFailedError
from ai.backend.common.types import DeviceName, KernelId, SessionTypes, SlotName


class _CreatedKernel(dict[str, Any]):
    """The kernel object `prepare_container` returns, as `create_kernel` uses it."""

    def __init__(self) -> None:
        super().__init__(container_id=None)
        self.session_type: SessionTypes | None = None
        self.data: dict[str, Any] = {}

    def set_container_id(self, cid: str) -> None:
        self["container_id"] = cid


class TestCreateKernelWhoseKernelIsCleanedUp:
    """Drives `AbstractAgent.create_kernel` itself up to `start_container`."""

    @staticmethod
    def _context(kernel_id: KernelId) -> MagicMock:
        ctx = MagicMock()
        ctx.kernel_id = kernel_id
        ctx.kernel_features = frozenset()
        ctx.get_overriding_uid.return_value = None
        ctx.get_overriding_gid.return_value = None
        ctx.get_supplementary_gids.return_value = []
        ctx.get_extra_envs = AsyncMock(return_value={})
        ctx.image_ref.architecture = "x86_64"
        ctx.image_ref.is_local = True
        resource_spec = MagicMock(mounts=[], allocations={DeviceName("cpu"): {SlotName("cpu"): {}}})
        ctx.generate_resource_spec = AsyncMock(return_value=(resource_spec, {}))
        ctx.get_intrinsic_mounts = AsyncMock(return_value=[])
        for name in (
            "prepare_scratch",
            "apply_network",
            "prepare_ssh",
            "mount_vfolders",
            "mount_krunner",
            "inject_additional_device_env_vars",
            "process_mounts",
        ):
            setattr(ctx, name, AsyncMock())
        ctx.kernel_config = {
            "cluster_role": "main",
            "preopen_ports": None,
            "allocated_host_ports": [],
        }
        ctx.prepare_container = AsyncMock(return_value=_CreatedKernel())
        return ctx

    @staticmethod
    def _creating_agent(ctx: MagicMock) -> Any:
        local_config = MagicMock()
        local_config.debug.log_kernel_config = False
        local_config.resource.allocation_order = []
        agent = SimpleNamespace(
            _active_creates={},
            local_config=local_config,
            kernel_registry={},
            restarting_kernels={},
            registry_lock=asyncio.Lock(),
            resource_lock=asyncio.Lock(),
            container_lifecycle_queue=asyncio.Queue(),
            computers={
                DeviceName("cpu"): MagicMock(
                    instance=MagicMock(get_attached_devices=AsyncMock(return_value=[]))
                )
            },
            affinity_map=MagicMock(),
            anycast_and_broadcast_event=AsyncMock(),
            init_kernel_context=AsyncMock(return_value=ctx),
            restart_kernel__store_config=AsyncMock(),
            reconstruct_resource_usage=AsyncMock(),
        )
        for name in ("track_create", "inject_container_lifecycle_event"):
            setattr(agent, name, functools.partial(getattr(AbstractAgent, name), cast(Any, agent)))
        return agent

    @pytest.fixture
    def kernel_id(self) -> KernelId:
        return KernelId(uuid.uuid4())

    @pytest.fixture
    def agent_whose_kernel_is_cleaned_up_during_the_start(self, kernel_id: KernelId) -> Any:
        ctx = self._context(kernel_id)
        agent = self._creating_agent(ctx)

        async def _starts_while_cleaned_up(*args: Any, **kwargs: Any) -> dict[str, Any]:
            agent.kernel_registry.pop(kernel_id)
            return {"container_id": "cid-1"}

        ctx.start_container = AsyncMock(side_effect=_starts_while_cleaned_up)
        return agent

    async def test_a_kernel_cleaned_up_during_the_start_fails_the_create_and_gets_no_destroy(
        self, kernel_id: KernelId, agent_whose_kernel_is_cleaned_up_during_the_start: Any
    ) -> None:
        agent = agent_whose_kernel_is_cleaned_up_during_the_start
        kernel_config = {
            "environ": {},
            "image": {"labels": {}, "digest": "sha256:0", "registry": {}},
            "resource_opts": {},
            "mounts": [],
            "session_type": SessionTypes.INTERACTIVE,
        }

        with (
            patch("ai.backend.agent.agent.get_arch_name", return_value="x86_64"),
            patch("ai.backend.agent.agent.allocate"),
            pytest.raises(ContainerCreationFailedError, match="Kernel cleaned up"),
        ):
            await AbstractAgent.create_kernel(
                agent,
                cast(Any, SimpleNamespace(kernel_id=kernel_id, session_id=uuid.uuid4())),
                MagicMock(),
                cast(Any, kernel_config),
                cast(Any, {"replicas": {}}),
            )

        assert agent.container_lifecycle_queue.empty()
