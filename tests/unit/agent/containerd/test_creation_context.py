from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext as Ctx
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.errors.containerd import ContainerdOperationFailed
from ai.backend.agent.resources import ComputerContext, KernelResourceSpec
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import (
    DeviceId,
    DeviceName,
    KernelCreationConfig,
    ResourceSlot,
    SlotName,
)

from .fakes import FakeContainerd

IMAGE = "cr.example.com/stable/python:3.11"


@pytest.fixture
def fake() -> FakeContainerd:
    fake = FakeContainerd()
    fake.add_image(
        IMAGE,
        diff_ids=["sha256:aa"],
        env=["PATH=/usr/bin", "LANG=C"],
        runtime={"Entrypoint": ["/bin/sh", "-c"], "Cmd": ["sleep 1"], "WorkingDir": "/srv"},
    )
    return fake


@pytest.fixture
def alloc_map() -> MagicMock:
    return MagicMock()


@pytest.fixture
def resource_spec() -> KernelResourceSpec:
    return KernelResourceSpec(
        slots=ResourceSlot({"cpu": "2", "mem": "1073741824"}),
        allocations={
            DeviceName("cpu"): {
                SlotName("cpu"): {DeviceId("1"): Decimal(1), DeviceId("3"): Decimal(1)}
            },
        },
        scratch_disk_size=0,
    )


@pytest.fixture
def ctx(
    ownership_data: KernelOwnershipData,
    fake: FakeContainerd,
    alloc_map: MagicMock,
) -> Ctx:
    local_config = MagicMock()
    local_config.container.sandbox_type = "docker"
    local_config.container.advertised_host = None
    local_config.container.bind_host = "10.0.0.5"
    computers = {DeviceName("cpu"): ComputerContext(MagicMock(), [], alloc_map)}
    config = cast(
        KernelCreationConfig,
        {
            "image": {"canonical": IMAGE, "labels": {}},
            "resource_slots": {"cpu": "1", "mem": "1073741824"},
            "resource_opts": {"shmem": "134217728"},
            "uid": None,
            "main_gid": None,
            "supplementary_gids": [],
            "internal_data": None,
            "network_id": "net-1",
            "environ": {},
            "mounts": [],
            "cluster_hostname": "main1",
        },
    )
    return Ctx(
        ownership_data,
        MagicMock(),
        MagicMock(),
        config,
        "ubuntu22.04",
        local_config,
        computers,
        client=fake,
        resource_lock=asyncio.Lock(),
    )


async def _prepare(ctx: Ctx, resource_spec: KernelResourceSpec) -> ContainerdKernel:
    return await ctx.prepare_container(
        resource_spec, {"LANG": "en_US.UTF-8", "LOCAL_USER_ID": "1000"}, [], MagicMock()
    )


class TestStartContainer:
    async def test_container_runs_the_image_command_on_runc(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        ownership_data: KernelOwnershipData,
    ) -> None:
        kernel = await _prepare(ctx, resource_spec)

        data = await ctx.start_container(kernel, [], None, [], MagicMock())

        cid = data["container_id"]
        assert cid.startswith(f"{ownership_data.kernel_id}-")
        assert data == {
            "container_id": cid,
            "kernel_host": "10.0.0.5",
            "repl_in_port": 0,
            "repl_out_port": 0,
            "stdin_port": 0,
            "stdout_port": 0,
        }
        runtime, raw_spec = fake.specs[cid]
        spec: dict[str, Any] = dict(raw_spec)
        assert runtime == "io.containerd.runc.v2"
        assert fake.tasks[cid].state.value == "running"
        assert spec["hostname"] == "main1"
        assert spec["linux"]["resources"]["cpu"]["cpus"] == "1,3"
        assert spec["process"]["args"] == ["/bin/sh", "-c", "sleep 1"]
        assert spec["process"]["cwd"] == "/srv"
        assert spec["process"]["env"] == ["PATH=/usr/bin", "LANG=en_US.UTF-8", "LOCAL_USER_ID=1000"]
        assert fake.containers[cid].labels["ai.backend.kernel-id"] == str(ownership_data.kernel_id)

    async def test_failed_launch_frees_the_allocations_and_leaves_nothing(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        alloc_map: MagicMock,
    ) -> None:
        kernel = await _prepare(ctx, resource_spec)
        fake.failing.add("create_task")

        with pytest.raises(ContainerdOperationFailed, match="create_task"):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        cast(MagicMock, alloc_map.free).assert_called_once()
        assert fake.containers == {} and fake.snapshots == {} and fake.tasks == {}

    async def test_cancelled_launch_frees_the_allocations_and_leaves_nothing(
        self,
        ctx: Ctx,
        resource_spec: KernelResourceSpec,
        fake: FakeContainerd,
        alloc_map: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        kernel = await _prepare(ctx, resource_spec)
        create_task = fake.create_task

        async def created_then_cancelled(*args: Any, **kwargs: Any) -> Any:
            await create_task(*args, **kwargs)
            raise asyncio.CancelledError

        monkeypatch.setattr(fake, "create_task", created_then_cancelled)

        with pytest.raises(asyncio.CancelledError):
            await ctx.start_container(kernel, [], None, [], MagicMock())

        alloc_map.free.assert_called_once()
        assert fake.containers == {} and fake.snapshots == {} and fake.tasks == {}
