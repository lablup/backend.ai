from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import LifecycleEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import ContainerId, KernelId, SessionId


class TestCreateKernelInitFailure:
    @pytest.mark.parametrize(
        ("failing_step", "error"),
        [
            ("init", RuntimeError("kernel init failed")),
            ("registry_update", RuntimeError("registry update failed")),
            ("init", asyncio.CancelledError()),
        ],
        ids=["init-error", "registry-update-error", "init-cancelled"],
    )
    async def test_failure_injects_failed_to_start_once(
        self, failing_step: str, error: BaseException
    ) -> None:
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())
        container_id = ContainerId("c0ffee")

        kernel_obj = MagicMock()
        if failing_step == "init":
            kernel_obj.init = AsyncMock(side_effect=error)
        else:
            kernel_obj.init = AsyncMock()
            kernel_obj.data.update.side_effect = error
        kernel_config: dict[str, object] = {
            "environ": {},
            "image": {"labels": {}, "digest": "sha256:0", "registry": {}},
            "mounts": [],
            "session_type": "interactive",
            "cluster_role": "main",
            "resource_opts": {},
            "preopen_ports": [],
            "allocated_host_ports": [],
        }

        resource_spec = MagicMock()
        resource_spec.allocations = {"cpu": {"cpu": []}}
        resource_spec.mounts = []

        ctx = MagicMock()
        ctx.kernel_id = kernel_id
        ctx.kernel_config = kernel_config
        ctx.get_overriding_uid.return_value = None
        ctx.get_overriding_gid.return_value = None
        ctx.get_supplementary_gids.return_value = []
        ctx.get_extra_envs = AsyncMock(return_value={})
        ctx.image_ref.architecture = "x86_64"
        ctx.image_ref.is_local = True
        ctx.generate_resource_spec = AsyncMock(return_value=(resource_spec, {}))
        for name in (
            "apply_network",
            "prepare_ssh",
            "inject_additional_device_env_vars",
            "process_mounts",
        ):
            setattr(ctx, name, AsyncMock())
        ctx.prepare_container = AsyncMock(return_value=kernel_obj)
        ctx.start_container = AsyncMock(return_value={"container_id": container_id})

        agent = MagicMock()
        agent.reported_creation_failures = set()

        @contextmanager
        def track_create(*_args: object, **_kwargs: object) -> Iterator[bool]:
            yield True

        agent.track_create = track_create
        agent.kernel_registry = {kernel_id: kernel_obj}
        agent.registry_lock = AsyncMock()
        agent.local_config.debug.log_kernel_config = False
        agent.local_config.debug.kernel_runner = False
        agent.local_config.container.sandbox_type = "docker"
        agent.local_config.container.jail_args = []
        agent.computers = {"cpu": MagicMock()}
        agent.computers["cpu"].instance.get_attached_devices = AsyncMock(return_value=[])
        agent.init_kernel_context = AsyncMock(return_value=ctx)
        agent.restart_kernel__store_config = AsyncMock()
        agent.inject_container_lifecycle_event = AsyncMock()
        agent.reconstruct_resource_usage = AsyncMock()

        ownership_data = MagicMock()
        ownership_data.kernel_id = kernel_id
        ownership_data.session_id = session_id
        cluster_info = MagicMock()

        with patch("ai.backend.agent.agent.get_arch_name", return_value="x86_64"):
            with pytest.raises(type(error)) as exc_info:
                await AbstractAgent.create_kernel(
                    agent,
                    ownership_data,
                    MagicMock(),
                    kernel_config,  # type: ignore[arg-type]
                    cluster_info,
                    restarting=True,
                )

        assert exc_info.value is error
        if failing_step == "init":
            kernel_obj.init.assert_awaited_once()
        else:
            kernel_obj.init.assert_not_awaited()
        assert agent.reported_creation_failures == {kernel_id}
        agent.inject_container_lifecycle_event.assert_awaited_once_with(
            kernel_id,
            session_id,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.FAILED_TO_START,
            container_id=container_id,
        )
