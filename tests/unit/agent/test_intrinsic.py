from __future__ import annotations

import asyncio
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import ai.backend.agent.intrinsic as intrinsic_mod
from ai.backend.agent.alloc_map import DiscretePropertyAllocMap
from ai.backend.agent.intrinsic import (
    ContainerNetStat,
    CPUPlugin,
    MemoryPlugin,
    read_proc_net_dev,
)
from ai.backend.agent.stats import StatModes
from ai.backend.agent.types import ContainerNetns
from ai.backend.common.types import DeviceId, DeviceName, SlotName


class BaseDockerIntrinsicTest:
    """Shared fixtures for Docker intrinsic plugin tests."""

    @pytest.fixture
    def container_ids(self) -> list[str]:
        return [f"container_{i:03d}" for i in range(5)]

    @pytest.fixture
    def docker_stats_response(self) -> dict[str, Any]:
        return {
            "read": "2024-01-01T00:00:00.000000000Z",
            "preread": "2024-01-01T00:00:01.000000000Z",
            "cpu_stats": {
                "cpu_usage": {
                    "total_usage": 1_000_000_000,
                },
            },
            "memory_stats": {
                "usage": 1024 * 1024 * 100,
                "limit": 1024 * 1024 * 1024,
            },
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "Read", "value": 1024},
                    {"op": "Write", "value": 2048},
                ],
            },
            "networks": {
                "eth0": {
                    "rx_bytes": 4096,
                    "tx_bytes": 8192,
                },
            },
        }

    @pytest.fixture
    def docker_stat_context(self) -> MagicMock:
        ctx = MagicMock()
        ctx.mode = StatModes.DOCKER
        return ctx

    @pytest.fixture
    def cgroup_stat_context(self) -> MagicMock:
        ctx = MagicMock()
        ctx.mode = StatModes.CGROUP
        return ctx


class TestPluginsHoldNoRuntimeClient(BaseDockerIntrinsicTest):
    """The intrinsic plugins must not own a container-runtime client.

    They used to construct an aiodocker `Docker()` in `init()`, which aborts when there is no
    /var/run/docker.sock — so a containerd-only node could not start its agent at all, even though
    these plugins only ever read cgroups.
    """

    async def test_cpu_init_needs_no_docker(self) -> None:
        plugin = CPUPlugin.__new__(CPUPlugin)
        plugin.local_config = {"agent": {}}
        await plugin.init()
        await plugin.cleanup()
        assert not hasattr(plugin, "_docker")

    async def test_memory_init_needs_no_docker(self) -> None:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {}}
        await plugin.init()
        await plugin.cleanup()
        assert not hasattr(plugin, "_docker")

    def test_module_constructs_no_docker_client(self) -> None:
        # Guards the regression directly: no `Docker(` call anywhere in the neutral module.
        source = Path(intrinsic_mod.__file__).read_text()
        assert "Docker()" not in source
        assert "DockerContainer(" not in source


class TestDockerStatModeGoesThroughTheAgent(BaseDockerIntrinsicTest):
    """StatModes.DOCKER samples come from the agent hook, not from a client the plugin owns."""

    @pytest.fixture
    def cpu_plugin(self) -> CPUPlugin:
        plugin = CPUPlugin.__new__(CPUPlugin)
        plugin.local_config = {"agent": {}}
        return plugin

    @pytest.fixture
    def memory_plugin(self) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {}}
        return plugin

    async def test_cpu_uses_the_agent_hook(
        self,
        cpu_plugin: CPUPlugin,
        container_ids: list[str],
        docker_stat_context: MagicMock,
        docker_stats_response: dict[str, Any],
    ) -> None:
        ctx = docker_stat_context
        ctx.agent.fetch_container_api_stats = AsyncMock(return_value=docker_stats_response)
        await cpu_plugin.gather_container_measures(ctx, container_ids)
        assert ctx.agent.fetch_container_api_stats.await_count == len(container_ids)

    async def test_memory_uses_the_agent_hook(
        self,
        memory_plugin: MemoryPlugin,
        container_ids: list[str],
        docker_stat_context: MagicMock,
        docker_stats_response: dict[str, Any],
    ) -> None:
        ctx = docker_stat_context
        ctx.agent.fetch_container_api_stats = AsyncMock(return_value=docker_stats_response)
        with patch("ai.backend.agent.intrinsic.current_loop") as mock_loop:

            async def run_in_executor(executor: Any, fn: Any, *args: Any) -> Any:
                return fn(*args)

            mock_loop.return_value.run_in_executor = AsyncMock(side_effect=run_in_executor)
            await memory_plugin.gather_container_measures(ctx, container_ids)
        assert ctx.agent.fetch_container_api_stats.await_count == len(container_ids)

    async def test_a_backend_without_an_api_yields_no_measures(
        self,
        cpu_plugin: CPUPlugin,
        container_ids: list[str],
        docker_stat_context: MagicMock,
    ) -> None:
        # The default hook returns None (containerd, k8s, dummy): no sample, no crash.
        ctx = docker_stat_context
        ctx.agent.fetch_container_api_stats = AsyncMock(return_value=None)
        measures = await cpu_plugin.gather_container_measures(ctx, container_ids)
        for m in measures:
            assert m.per_container == {}


class TestMemoryPluginContainerPidValidation(BaseDockerIntrinsicTest):
    """Tests for container PID validation before reading /proc/[pid]/net/dev."""

    @pytest.fixture
    def memory_plugin(self) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        return plugin

    @contextmanager
    def _make_cgroup_context(
        self,
        cgroup_stat_context: MagicMock,
        container_pid: int,
    ) -> Generator[tuple[MagicMock, MagicMock], None, None]:
        """Build a CGROUP stat context with configurable container PID.

        PID=0 means container not running (skips read_proc_net_dev).
        PID>0 calls read_proc_net_dev via executor.
        """
        ctx = cgroup_stat_context
        ctx.agent.get_cgroup_version = MagicMock(return_value="2")

        mem_path = MagicMock()
        mem_stat = MagicMock()
        mem_stat.read_text.return_value = "inactive_file 0\n"
        mem_path.__truediv__ = MagicMock(return_value=mem_stat)
        io_path = MagicMock()
        io_stat = MagicMock()
        io_stat.read_text.return_value = ""
        io_path.__truediv__ = MagicMock(return_value=io_stat)

        def mock_get_cgroup_path(subsys: str, cid: str) -> MagicMock:
            if subsys == "memory":
                return mem_path
            return io_path

        ctx.agent.get_cgroup_path = mock_get_cgroup_path

        # The backend reports how to reach the container's netns; the plugin no longer inspects
        # the container through the Docker API itself.
        ctx.agent.get_container_netns = AsyncMock(
            return_value=ContainerNetns(pid=container_pid, path=None)
        )

        with (
            patch(
                "ai.backend.agent.intrinsic.read_sysfs",
                return_value=1048576,
            ),
            patch(
                "ai.backend.agent.intrinsic.read_proc_net_dev",
            ) as mock_read_proc_net_dev,
            patch(
                "ai.backend.agent.intrinsic.current_loop",
            ) as mock_loop,
        ):
            mock_read_proc_net_dev.return_value = ContainerNetStat(rx_bytes=4096, tx_bytes=8192)

            async def run_in_executor_impl(executor: Any, fn: Any, *args: Any) -> Any:
                return fn(*args)

            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=run_in_executor_impl,
            )
            yield ctx, mock_read_proc_net_dev

    async def test_pid_zero_returns_zero_net_stats(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
    ) -> None:
        """When container PID is 0 (not running), net stats should be 0
        but other stats collected."""
        with self._make_cgroup_context(
            cgroup_stat_context,
            container_pid=0,
        ) as (ctx, mock_read):
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            mock_read.assert_not_called()
            # mem stats should be collected (read_sysfs returns 1048576)
            assert results[0].per_container["cid_001"].value == 1048576
            # net_rx and net_tx should be 0
            assert results[3].per_container["cid_001"].value == 0
            assert results[4].per_container["cid_001"].value == 0

    async def test_valid_pid_calls_read_proc_net_dev(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
    ) -> None:
        """When container PID > 0, read_proc_net_dev should be called
        and net stats collected."""
        with self._make_cgroup_context(
            cgroup_stat_context,
            container_pid=12345,
        ) as (ctx, mock_read):
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            mock_read.assert_called_once_with(12345)
            # mem stats should be collected
            assert results[0].per_container["cid_001"].value == 1048576
            # net_rx and net_tx should have values from mock read_proc_net_dev
            assert results[3].per_container["cid_001"].value == 4096
            assert results[4].per_container["cid_001"].value == 8192

    async def test_oserror_returns_zero_net_stats(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
    ) -> None:
        """When read_proc_net_dev raises OSError, net stats should be 0
        but other stats collected."""
        with self._make_cgroup_context(
            cgroup_stat_context,
            container_pid=12345,
        ) as (ctx, mock_read):
            mock_read.side_effect = OSError("No such file or directory")
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            # mem stats should be collected
            assert results[0].per_container["cid_001"].value == 1048576
            # net_rx and net_tx should be 0 due to OSError fallback
            assert results[3].per_container["cid_001"].value == 0
            assert results[4].per_container["cid_001"].value == 0


@dataclass
class _SysfsMocks:
    ctx: MagicMock
    get_container_netns: AsyncMock
    read_proc_net_dev: MagicMock
    loop: MagicMock


class TestMemoryPluginSysfsTimeoutAndErrorIsolation(BaseDockerIntrinsicTest):
    """Tests for timeout protection and error isolation in MemoryPlugin sysfs_impl."""

    @pytest.fixture
    def memory_plugin(self) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        return plugin

    @pytest.fixture
    def sysfs_mocks(self, cgroup_stat_context: MagicMock) -> Generator[_SysfsMocks, None, None]:
        """Fully patched sysfs_impl environment with default happy-path behavior.

        Tests override specific mock side_effects before calling the target function.
        """
        ctx = cgroup_stat_context
        ctx.agent.get_cgroup_version = MagicMock(return_value="2")

        mem_path = MagicMock()
        mem_stat = MagicMock()
        mem_stat.read_text.return_value = "inactive_file 0\n"
        mem_path.__truediv__ = MagicMock(return_value=mem_stat)
        io_path = MagicMock()
        io_stat = MagicMock()
        io_stat.read_text.return_value = ""
        io_path.__truediv__ = MagicMock(return_value=io_stat)
        ctx.agent.get_cgroup_path = lambda subsys, cid: mem_path if subsys == "memory" else io_path

        get_container_netns = AsyncMock(return_value=ContainerNetns(pid=12345, path=None))
        ctx.agent.get_container_netns = get_container_netns

        with (
            patch("ai.backend.agent.intrinsic.read_sysfs", return_value=1048576),
            patch(
                "ai.backend.agent.intrinsic.read_proc_net_dev",
                return_value=ContainerNetStat(rx_bytes=0, tx_bytes=0),
            ) as mock_read_proc_net_dev,
            patch("ai.backend.agent.intrinsic.current_loop") as mock_loop,
        ):

            async def default_run_in_executor(executor: Any, fn: Any, *args: Any) -> Any:
                return fn(*args)

            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=default_run_in_executor,
            )

            yield _SysfsMocks(
                ctx=ctx,
                get_container_netns=get_container_netns,
                read_proc_net_dev=mock_read_proc_net_dev,
                loop=mock_loop,
            )

    async def test_slow_get_container_netns_times_out(
        self,
        memory_plugin: MemoryPlugin,
        sysfs_mocks: _SysfsMocks,
    ) -> None:
        """When the backend hangs resolving the container's netns, the call times out and returns
        None for that container while other containers succeed."""

        async def slow_for_first(container_id: str) -> ContainerNetns:
            if container_id == "slow_container":
                await asyncio.sleep(10)
            return ContainerNetns(pid=12345, path=None)

        sysfs_mocks.get_container_netns.side_effect = slow_for_first

        results = await memory_plugin.gather_container_measures(
            sysfs_mocks.ctx, ["slow_container", "normal_container"]
        )

        assert "slow_container" not in results[0].per_container
        assert "normal_container" in results[0].per_container

    async def test_pinned_netns_is_used_when_the_pid_is_gone(
        self,
        memory_plugin: MemoryPlugin,
        sysfs_mocks: _SysfsMocks,
        tmp_path: Path,
    ) -> None:
        """A container whose main process is gone but whose netns is still pinned must have its
        counters read through the namespace path instead of /proc/<pid>/net/dev."""
        ns_path = tmp_path / "netns"
        ns_path.touch()
        sysfs_mocks.get_container_netns.return_value = ContainerNetns(pid=None, path=ns_path)

        with patch(
            "ai.backend.agent.intrinsic.read_netns_net_dev",
            return_value=ContainerNetStat(rx_bytes=111, tx_bytes=222),
        ) as mock_read_netns:
            results = await memory_plugin.gather_container_measures(sysfs_mocks.ctx, ["cid_001"])

        mock_read_netns.assert_called_once_with(ns_path)
        sysfs_mocks.read_proc_net_dev.assert_not_called()
        assert results[3].per_container["cid_001"].value == 111
        assert results[4].per_container["cid_001"].value == 222

    async def test_gather_isolates_container_failures(
        self,
        memory_plugin: MemoryPlugin,
        sysfs_mocks: _SysfsMocks,
    ) -> None:
        """When one container raises an Exception subclass, it is logged and
        skipped while other containers are still collected.

        Uses RuntimeError (not OSError) because OSError is caught inside
        sysfs_impl and returns None — it never reaches the Exception
        branch in the results loop.
        """

        async def selective_run_in_executor(executor: Any, fn: Any, *args: Any) -> Any:
            if args and args[0] == "broken_container":
                raise RuntimeError("unexpected executor failure")
            return fn(*args)

        sysfs_mocks.loop.return_value.run_in_executor = selective_run_in_executor

        results = await memory_plugin.gather_container_measures(
            sysfs_mocks.ctx, ["broken_container", "healthy_container"]
        )

        assert "broken_container" not in results[0].per_container
        assert "healthy_container" in results[0].per_container

    async def test_cancelled_error_is_reraised(
        self,
        memory_plugin: MemoryPlugin,
        sysfs_mocks: _SysfsMocks,
    ) -> None:
        """When a container task raises CancelledError (a BaseException but not
        Exception), it must propagate instead of being silently skipped.
        This ensures shutdown signals are not swallowed by return_exceptions=True."""

        async def cancel_on_first(executor: Any, fn: Any, *args: Any) -> Any:
            if args and args[0] == "cancelled_container":
                raise asyncio.CancelledError()
            return fn(*args)

        sysfs_mocks.loop.return_value.run_in_executor = cancel_on_first

        with pytest.raises(asyncio.CancelledError):
            await memory_plugin.gather_container_measures(
                sysfs_mocks.ctx, ["cancelled_container", "healthy_container"]
            )


class TestReadProcNetDev:
    """Tests for read_proc_net_dev() parsing /proc/[pid]/net/dev format."""

    SAMPLE_NET_DEV = (
        "Inter-|   Receive                                                |  Transmit\n"
        " face |bytes    packets errs drop fifo frame compressed multicast"
        "|bytes    packets errs drop fifo colls carrier compressed\n"
        "    lo:    1234       10    0    0    0     0          0         0"
        "        5678       10    0    0    0     0       0          0\n"
        "  eth0:   50000      100    0    0    0     0          0         0"
        "       80000      200    0    0    0     0       0          0\n"
    )

    MULTI_IFACE_NET_DEV = (
        "Inter-|   Receive                                                |  Transmit\n"
        " face |bytes    packets errs drop fifo frame compressed multicast"
        "|bytes    packets errs drop fifo colls carrier compressed\n"
        "    lo:       0        0    0    0    0     0          0         0"
        "           0        0    0    0    0     0       0          0\n"
        "  eth0:   10000       50    0    0    0     0          0         0"
        "       20000      100    0    0    0     0       0          0\n"
        "  eth1:   30000       70    0    0    0     0          0         0"
        "       40000      150    0    0    0     0       0          0\n"
    )

    LO_ONLY_NET_DEV = (
        "Inter-|   Receive                                                |  Transmit\n"
        " face |bytes    packets errs drop fifo frame compressed multicast"
        "|bytes    packets errs drop fifo colls carrier compressed\n"
        "    lo:    9999       10    0    0    0     0          0         0"
        "        8888       10    0    0    0     0       0          0\n"
    )

    @pytest.mark.parametrize(
        ("content_attr", "expected_rx", "expected_tx"),
        [
            ("SAMPLE_NET_DEV", 50000, 80000),
            ("MULTI_IFACE_NET_DEV", 40000, 60000),
            ("LO_ONLY_NET_DEV", 0, 0),
        ],
        ids=["standard_format", "multiple_interfaces", "loopback_only"],
    )
    def test_parse_net_dev(
        self,
        tmp_path: Path,
        content_attr: str,
        expected_rx: int,
        expected_tx: int,
    ) -> None:
        net_dev = tmp_path / "net_dev"
        net_dev.write_text(getattr(self, content_attr))
        with patch(
            "ai.backend.agent.intrinsic.Path",
            return_value=net_dev,
        ):
            result = read_proc_net_dev(42)
        assert result.rx_bytes == expected_rx
        assert result.tx_bytes == expected_tx

    def test_raises_oserror_for_nonexistent_pid(self) -> None:
        """Raises OSError when /proc/[pid]/net/dev does not exist."""
        with pytest.raises(OSError):
            read_proc_net_dev(999999999)


class TestMemoryRestoreFromContainer:
    """restore_from_container must be backend-agnostic: it reads our own resource record
    (resource.txt) rather than a Docker-specific HostConfig.Memory, so the containerd backend
    (which has no HostConfig) can restore allocations on agent restart."""

    async def test_reads_resource_spec_not_hostconfig(self, monkeypatch: Any) -> None:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        # No HostConfig["Memory"] here: reading it (the old behavior) would KeyError.
        container = MagicMock()
        container.backend_obj = {"HostConfig": {"Mounts": []}}
        alloc = {DeviceId("root"): Decimal(2 * 2**30)}
        spec = MagicMock()
        spec.allocations = {DeviceName("mem"): {SlotName("mem"): alloc}}
        monkeypatch.setattr(
            "ai.backend.agent.intrinsic.get_resource_spec_from_container",
            AsyncMock(return_value=spec),
        )
        alloc_map = MagicMock(spec=DiscretePropertyAllocMap)
        await plugin.restore_from_container(container, alloc_map)
        alloc_map.apply_allocation.assert_called_once_with({SlotName("mem"): alloc})

    async def test_noop_when_resource_spec_missing(self, monkeypatch: Any) -> None:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        monkeypatch.setattr(
            "ai.backend.agent.intrinsic.get_resource_spec_from_container",
            AsyncMock(return_value=None),
        )
        alloc_map = MagicMock(spec=DiscretePropertyAllocMap)
        await plugin.restore_from_container(MagicMock(), alloc_map)
        alloc_map.apply_allocation.assert_not_called()
