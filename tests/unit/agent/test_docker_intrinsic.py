from __future__ import annotations

import asyncio
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.docker.intrinsic import (
    ContainerNetStat,
    CPUPlugin,
    MemoryPlugin,
    read_proc_net_dev,
)
from ai.backend.agent.stats import StatModes


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

    @pytest.fixture
    def mock_fetch_api_stats(
        self, docker_stats_response: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        with patch(
            "ai.backend.agent.docker.intrinsic.fetch_api_stats",
            return_value=docker_stats_response,
        ) as mock:
            yield mock


class TestCPUPluginDockerClientLifecycle(BaseDockerIntrinsicTest):
    """Tests for CPUPlugin Docker client lifecycle management."""

    @pytest.fixture
    def cpu_plugin(self) -> CPUPlugin:
        plugin = CPUPlugin.__new__(CPUPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
        return plugin

    @pytest.fixture
    def cpu_cgroup_context(self, cgroup_stat_context: MagicMock) -> MagicMock:
        """CGROUP stat context with CPU cgroup v2 path mocks."""
        cgroup_stat_context.agent.docker_info = {"CgroupVersion": "2"}

        def mock_get_cgroup_path(subsys: str, cid: str) -> MagicMock:
            path = MagicMock()
            stat_file = MagicMock()
            stat_file.read_text.return_value = "usage_usec 1000000\n"
            path.__truediv__ = MagicMock(return_value=stat_file)
            return path

        cgroup_stat_context.agent.get_cgroup_path = mock_get_cgroup_path
        return cgroup_stat_context

    async def test_init_creates_docker_client(self, cpu_plugin: CPUPlugin) -> None:
        """Verify init() creates a Docker client instance."""
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            mock_docker_cls.return_value = AsyncMock()
            await cpu_plugin.init()
            mock_docker_cls.assert_called_once()
            assert cpu_plugin._docker is not None

    async def test_cleanup_closes_docker_client(self, cpu_plugin: CPUPlugin) -> None:
        """Verify cleanup() closes the Docker client."""
        cpu_plugin._docker = AsyncMock()
        await cpu_plugin.cleanup()
        cpu_plugin._docker.close.assert_called_once()

    async def test_api_mode_uses_instance_docker_client(
        self,
        cpu_plugin: CPUPlugin,
        container_ids: list[str],
        docker_stat_context: MagicMock,
        mock_fetch_api_stats: MagicMock,
    ) -> None:
        """Verify API mode uses the plugin's Docker client, not a new one."""
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            await cpu_plugin.gather_container_measures(docker_stat_context, container_ids)
            mock_docker_cls.assert_not_called()

    async def test_sysfs_mode_does_not_use_docker(
        self,
        cpu_plugin: CPUPlugin,
        container_ids: list[str],
        cpu_cgroup_context: MagicMock,
    ) -> None:
        """Verify CGROUP mode doesn't create any new Docker instance."""
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            await cpu_plugin.gather_container_measures(cpu_cgroup_context, container_ids)
            mock_docker_cls.assert_not_called()


class TestMemoryPluginDockerClientLifecycle(BaseDockerIntrinsicTest):
    """Tests for MemoryPlugin Docker client lifecycle management."""

    @pytest.fixture
    def memory_plugin(self) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
        return plugin

    @pytest.fixture
    def memory_cgroup_context(
        self, cgroup_stat_context: MagicMock
    ) -> Generator[MagicMock, None, None]:
        """CGROUP stat context with memory/io cgroup v2 path mocks and related patches."""
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

        mock_container_data = {
            "State": {"Pid": 12345},
        }

        with (
            patch(
                "ai.backend.agent.docker.intrinsic.DockerContainer",
            ) as mock_container_cls,
            patch(
                "ai.backend.agent.docker.intrinsic.read_sysfs",
                return_value=1048576,
            ),
            patch(
                "ai.backend.agent.docker.intrinsic.read_proc_net_dev",
                return_value=ContainerNetStat(rx_bytes=0, tx_bytes=0),
            ),
            patch(
                "ai.backend.agent.docker.intrinsic.current_loop",
            ) as mock_loop,
        ):
            mock_container_instance = AsyncMock()
            mock_container_instance.show.return_value = mock_container_data
            mock_container_cls.return_value = mock_container_instance

            async def default_run_in_executor(executor: Any, fn: Any, *args: Any) -> Any:
                return fn(*args)

            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=default_run_in_executor,
            )
            yield ctx

    async def test_init_creates_docker_client(self, memory_plugin: MemoryPlugin) -> None:
        """Verify init() creates a Docker client instance."""
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            mock_docker_cls.return_value = AsyncMock()
            await memory_plugin.init()
            mock_docker_cls.assert_called_once()
            assert memory_plugin._docker is not None

    async def test_cleanup_closes_docker_client(self, memory_plugin: MemoryPlugin) -> None:
        """Verify cleanup() closes the Docker client."""
        memory_plugin._docker = AsyncMock()
        await memory_plugin.cleanup()
        memory_plugin._docker.close.assert_called_once()

    async def test_api_mode_uses_instance_docker_client(
        self,
        memory_plugin: MemoryPlugin,
        container_ids: list[str],
        docker_stat_context: MagicMock,
        mock_fetch_api_stats: MagicMock,
    ) -> None:
        """Verify API mode uses the plugin's Docker client, not a new one."""
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            await memory_plugin.gather_container_measures(docker_stat_context, container_ids)
            mock_docker_cls.assert_not_called()

    async def test_sysfs_mode_uses_instance_docker_client(
        self,
        memory_plugin: MemoryPlugin,
        container_ids: list[str],
        memory_cgroup_context: MagicMock,
    ) -> None:
        """Even in CGROUP mode, Docker is needed for container PID. Verify instance client is used."""
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            await memory_plugin.gather_container_measures(memory_cgroup_context, container_ids)
            mock_docker_cls.assert_not_called()


class TestMemoryPluginContainerPidValidation(BaseDockerIntrinsicTest):
    """Tests for container PID validation before reading /proc/[pid]/net/dev."""

    @pytest.fixture
    def memory_plugin(self) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
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

        mock_container_data = {
            "State": {"Pid": container_pid},
        }

        with (
            patch(
                "ai.backend.agent.docker.intrinsic.DockerContainer",
            ) as mock_container_cls,
            patch(
                "ai.backend.agent.docker.intrinsic.read_sysfs",
                return_value=1048576,
            ),
            patch(
                "ai.backend.agent.docker.intrinsic.read_proc_net_dev",
            ) as mock_read_proc_net_dev,
            patch(
                "ai.backend.agent.docker.intrinsic.current_loop",
            ) as mock_loop,
        ):
            mock_read_proc_net_dev.return_value = ContainerNetStat(rx_bytes=4096, tx_bytes=8192)

            async def run_in_executor_impl(executor: Any, fn: Any, *args: Any) -> Any:
                return fn(*args)

            mock_container_instance = AsyncMock()
            mock_container_instance.show.return_value = mock_container_data
            mock_container_cls.return_value = mock_container_instance
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
    container: AsyncMock
    read_proc_net_dev: MagicMock
    loop: MagicMock
    container_data: dict[str, Any]


class TestMemoryPluginSysfsTimeoutAndErrorIsolation(BaseDockerIntrinsicTest):
    """Tests for timeout protection and error isolation in MemoryPlugin sysfs_impl."""

    @pytest.fixture
    def memory_plugin(self) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
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

        container_data: dict[str, Any] = {
            "State": {"Pid": 12345},
        }

        with (
            patch(
                "ai.backend.agent.docker.intrinsic.DockerContainer",
            ) as mock_container_cls,
            patch("ai.backend.agent.docker.intrinsic.read_sysfs", return_value=1048576),
            patch(
                "ai.backend.agent.docker.intrinsic.read_proc_net_dev",
                return_value=ContainerNetStat(rx_bytes=0, tx_bytes=0),
            ) as mock_read_proc_net_dev,
            patch("ai.backend.agent.docker.intrinsic.current_loop") as mock_loop,
        ):
            mock_container = AsyncMock()
            mock_container.show.return_value = container_data
            mock_container_cls.return_value = mock_container

            async def default_run_in_executor(executor: Any, fn: Any, *args: Any) -> Any:
                return fn(*args)

            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=default_run_in_executor,
            )

            yield _SysfsMocks(
                ctx=ctx,
                container=mock_container,
                read_proc_net_dev=mock_read_proc_net_dev,
                loop=mock_loop,
                container_data=container_data,
            )

    async def test_slow_container_show_times_out(
        self,
        memory_plugin: MemoryPlugin,
        sysfs_mocks: _SysfsMocks,
    ) -> None:
        """When container.show() hangs, the call times out and returns None
        for that container while other containers succeed."""
        call_count = 0

        async def slow_show_for_first(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(10)
            return sysfs_mocks.container_data

        sysfs_mocks.container.show.side_effect = slow_show_for_first

        results = await memory_plugin.gather_container_measures(
            sysfs_mocks.ctx, ["slow_container", "normal_container"]
        )

        assert "slow_container" not in results[0].per_container
        assert "normal_container" in results[0].per_container

    async def test_slow_container_show_for_net_stats_times_out(
        self,
        memory_plugin: MemoryPlugin,
        sysfs_mocks: _SysfsMocks,
    ) -> None:
        """When container.show() hangs during net stat collection,
        the call times out and returns None for that container
        while other containers succeed."""
        call_count = 0

        async def slow_show_on_second_call(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            # First call succeeds quickly, second call hangs
            if call_count == 1:
                await asyncio.sleep(10)
            return sysfs_mocks.container_data

        sysfs_mocks.container.show.side_effect = slow_show_on_second_call

        results = await memory_plugin.gather_container_measures(
            sysfs_mocks.ctx, ["slow_container", "normal_container"]
        )

        assert "slow_container" not in results[0].per_container
        assert "normal_container" in results[0].per_container

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
            "ai.backend.agent.docker.intrinsic.Path",
            return_value=net_dev,
        ):
            result = read_proc_net_dev(42)
        assert result.rx_bytes == expected_rx
        assert result.tx_bytes == expected_tx

    def test_raises_oserror_for_nonexistent_pid(self) -> None:
        """Raises OSError when /proc/[pid]/net/dev does not exist."""
        with pytest.raises(OSError):
            read_proc_net_dev(999999999)
