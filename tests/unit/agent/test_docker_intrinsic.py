from __future__ import annotations

import asyncio
import logging
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiodocker.exceptions import DockerError

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.agent.docker.intrinsic import (
    ContainerNetStat,
    CPUPlugin,
    DockerStatsStreamer,
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

    def _make_prewarmed_streamer(
        self,
        sample: dict[str, Any] | None,
    ) -> MagicMock:
        streamer = MagicMock(spec=DockerStatsStreamer)
        streamer.get_latest = MagicMock(return_value=sample)
        return streamer


class TestCPUPluginDockerClientLifecycle(BaseDockerIntrinsicTest):
    """Tests for CPUPlugin Docker client lifecycle management."""

    @pytest.fixture
    def cpu_plugin(self, docker_stats_response: dict[str, Any]) -> CPUPlugin:
        plugin = CPUPlugin.__new__(CPUPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
        plugin._stats_streamer = self._make_prewarmed_streamer(docker_stats_response)
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
    def memory_plugin(self, docker_stats_response: dict[str, Any]) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
        plugin._stats_streamer = self._make_prewarmed_streamer(docker_stats_response)
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
    def memory_plugin(self, docker_stats_response: dict[str, Any]) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
        plugin._stats_streamer = self._make_prewarmed_streamer(docker_stats_response)
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
    def memory_plugin(self, docker_stats_response: dict[str, Any]) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
        plugin._stats_streamer = self._make_prewarmed_streamer(docker_stats_response)
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


class _FakeDockerContainer:
    """Lightweight stand-in for :class:`aiodocker.docker.DockerContainer`.

    Each instance yields frames from a caller-supplied async-iter factory,
    allowing tests to simulate transient errors, partial streams, and
    graceful upstream shutdowns.
    """

    def __init__(self, frame_source: Any, container_id: str) -> None:
        self._frame_source = frame_source
        self.id = container_id

    def stats(self, *, stream: bool = True) -> Any:
        # aiodocker's .stats() returns an async iterable directly.
        return self._frame_source(self.id)


@pytest.fixture
def sample_stats_frame() -> dict[str, Any]:
    return {
        "read": "2024-01-01T00:00:00.000000000Z",
        "preread": "2024-01-01T00:00:01.000000000Z",
        "cpu_stats": {"cpu_usage": {"total_usage": 1_000_000_000}},
        "memory_stats": {"usage": 1024, "limit": 4096},
    }


async def _poll_for_latest(
    streamer: DockerStatsStreamer,
    container_id: str,
    timeout: float = 2.0,
) -> dict[str, Any] | None:
    """Poll ``streamer.get_latest`` until it returns a non-None value or timeout."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        sample = streamer.get_latest(container_id)
        if sample is not None:
            return sample
        await asyncio.sleep(0)
    return streamer.get_latest(container_id)


class TestDockerStatsStreamerLifecycle:
    """Tests for eager start/stop lifecycle of :class:`DockerStatsStreamer`."""

    async def test_start_spawns_reader_and_first_sample_lands(
        self, sample_stats_frame: dict[str, Any]
    ) -> None:
        """After start(), a reader task is created and the first emitted
        frame lands in the cache."""
        first_emitted = asyncio.Event()
        hold_open = asyncio.Event()

        async def frames(_cid: str) -> Any:
            yield sample_stats_frame
            first_emitted.set()
            # Keep the stream open until the test explicitly ends it.
            await hold_open.wait()

        def fake_container_cls(docker: Any, id: str) -> _FakeDockerContainer:
            return _FakeDockerContainer(frames, id)

        with patch(
            "ai.backend.agent.docker.intrinsic.DockerContainer",
            side_effect=fake_container_cls,
        ):
            streamer = DockerStatsStreamer(AsyncMock())
            streamer.start("cid_000")
            assert "cid_000" in streamer._tasks
            sample = await _poll_for_latest(streamer, "cid_000", timeout=2.0)
            assert sample == sample_stats_frame
            hold_open.set()
            await streamer.close()

    async def test_stop_cancels_reader_and_drops_cache(
        self, sample_stats_frame: dict[str, Any]
    ) -> None:
        """stop() cancels the in-flight reader task and removes the cached sample."""
        hold_open = asyncio.Event()

        async def frames(_cid: str) -> Any:
            yield sample_stats_frame
            await hold_open.wait()

        def fake_container_cls(docker: Any, id: str) -> _FakeDockerContainer:
            return _FakeDockerContainer(frames, id)

        with patch(
            "ai.backend.agent.docker.intrinsic.DockerContainer",
            side_effect=fake_container_cls,
        ):
            streamer = DockerStatsStreamer(AsyncMock())
            streamer.start("cid_000")
            await _poll_for_latest(streamer, "cid_000", timeout=2.0)
            task = streamer._tasks["cid_000"]
            await streamer.stop("cid_000")
            assert "cid_000" not in streamer._tasks
            assert streamer.get_latest("cid_000") is None
            assert task.done()

    async def test_close_cancels_all_in_flight_tasks(self) -> None:
        """close() cancels every reader task and clears state."""
        hold_open = asyncio.Event()

        async def frames(_cid: str) -> Any:
            # Yield an infinite stream that the test never releases.
            while True:
                await hold_open.wait()
                yield {"read": "2024-01-01T00:00:00.000000000Z", "preread": "0001-01-01T00:00:00Z"}

        def fake_container_cls(docker: Any, id: str) -> _FakeDockerContainer:
            return _FakeDockerContainer(frames, id)

        with patch(
            "ai.backend.agent.docker.intrinsic.DockerContainer",
            side_effect=fake_container_cls,
        ):
            streamer = DockerStatsStreamer(AsyncMock())
            for cid in ("cid_a", "cid_b", "cid_c"):
                streamer.start(cid)
            tasks = list(streamer._tasks.values())
            assert len(tasks) == 3
            await streamer.close()
            for task in tasks:
                assert task.done()
            assert streamer._tasks == {}
            assert streamer._latest == {}


class TestDockerStatsStreamerReconnect:
    """Tests for reconnect-with-backoff behaviour on transient transport failures."""

    async def test_reconnect_after_client_connection_error(
        self, sample_stats_frame: dict[str, Any]
    ) -> None:
        """When the stream raises ClientConnectionError once, the reader
        sleeps briefly then reopens and eventually publishes a sample."""
        call_count = 0

        async def frames(_cid: str) -> Any:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise aiohttp_client_connection_error("daemon dropped the stream")
            yield sample_stats_frame
            await asyncio.Event().wait()

        def fake_container_cls(docker: Any, id: str) -> _FakeDockerContainer:
            return _FakeDockerContainer(frames, id)

        # Monkey-patch asyncio.sleep to make backoff zero-cost for the test.
        orig_sleep = asyncio.sleep

        async def fast_sleep(delay: float) -> None:
            await orig_sleep(0)

        with (
            patch(
                "ai.backend.agent.docker.intrinsic.DockerContainer",
                side_effect=fake_container_cls,
            ),
            patch("ai.backend.agent.docker.intrinsic.asyncio.sleep", fast_sleep),
        ):
            streamer = DockerStatsStreamer(AsyncMock())
            streamer.start("cid_000")
            sample = await _poll_for_latest(streamer, "cid_000", timeout=2.0)
            assert sample == sample_stats_frame
            assert call_count >= 2
            await streamer.close()

    async def test_cancelled_error_reraises_from_reader(self) -> None:
        """Cancelling the reader task via close() unwinds it cleanly and does
        NOT swallow CancelledError inside the reader (it propagates to .cancel())."""

        entered = asyncio.Event()
        sentinel: dict[str, Any] = {}

        async def frames(_cid: str) -> Any:
            entered.set()
            # Park forever until cancelled; the final yield is unreachable
            # but keeps this function an async generator.
            try:
                await asyncio.Event().wait()
            finally:
                # The reader's finally block must also run after CancelledError.
                pass
            yield sentinel

        def fake_container_cls(docker: Any, id: str) -> _FakeDockerContainer:
            return _FakeDockerContainer(frames, id)

        with patch(
            "ai.backend.agent.docker.intrinsic.DockerContainer",
            side_effect=fake_container_cls,
        ):
            streamer = DockerStatsStreamer(AsyncMock())
            streamer.start("cid_000")
            await entered.wait()
            task = streamer._tasks["cid_000"]
            await streamer.close()
            assert task.done()
            assert task.cancelled() or task.exception() is None

    async def test_reader_exits_cleanly_on_container_gone_404(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """DockerError 404 from the stats stream means the container is gone:
        the reader must exit cleanly (no retry spin, no warning-level log)."""

        call_count = 0

        async def frames(_cid: str) -> Any:
            nonlocal call_count
            call_count += 1
            # Raise on the very first iteration to simulate an already-gone
            # container. A no-op ``yield`` in an unreachable branch keeps this
            # function an async generator without tripping ``unreachable`` mypy.
            if call_count < 0:
                yield {}
            raise DockerError(404, {"message": "No such container"})

        def fake_container_cls(docker: Any, id: str) -> _FakeDockerContainer:
            return _FakeDockerContainer(frames, id)

        with (
            patch(
                "ai.backend.agent.docker.intrinsic.DockerContainer",
                side_effect=fake_container_cls,
            ),
            caplog.at_level(logging.DEBUG, logger="ai.backend.agent.docker.intrinsic"),
        ):
            streamer = DockerStatsStreamer(AsyncMock())
            streamer.start("cid_gone")
            task = streamer._tasks["cid_gone"]
            # The reader must exit on its own; 404 must NOT spin in the retry loop.
            await asyncio.wait_for(task, timeout=2.0)
            assert task.done()
            assert not task.cancelled()
            assert task.exception() is None
            # Only one stream-open attempt; no reconnect/retry on 404.
            assert call_count == 1
            # ``get_latest`` may re-spawn a reader as a safety net, but the
            # cached sample was dropped in the reader's finally block and the
            # respawned reader will hit the same 404 path, so the return value
            # is still ``None``.
            assert streamer._latest.get("cid_gone") is None
            await streamer.close()
            # 404 is a debug-level path; container-gone is not an error.
            intrinsic_records = [
                r for r in caplog.records if r.name == "ai.backend.agent.docker.intrinsic"
            ]
            for record in intrinsic_records:
                assert record.levelno < logging.WARNING, (
                    f"unexpected warning-or-above log: {record.levelname} {record.getMessage()}"
                )
            assert streamer.get_latest("cid_gone") is None


class TestSharedStatsStreamerWiring:
    """Verify the agent owns a single streamer that both intrinsic plugins share."""

    async def test_agent_owns_single_statsstreamer_shared_with_plugins(self) -> None:
        """After :meth:`DockerAgent.attach_stats_streamer` is called for each
        intrinsic plugin, both plugins must reference the SAME streamer
        instance that the agent owns on ``self._stats_streamer``."""
        streamer = DockerStatsStreamer(AsyncMock())

        cpu_plugin = CPUPlugin.__new__(CPUPlugin)
        mem_plugin = MemoryPlugin.__new__(MemoryPlugin)
        cpu_plugin.attach_stats_streamer(streamer)
        mem_plugin.attach_stats_streamer(streamer)

        assert cpu_plugin._stats_streamer is streamer
        assert mem_plugin._stats_streamer is streamer
        assert cpu_plugin._stats_streamer is mem_plugin._stats_streamer

    async def test_agent_stats_streamer_closed_on_shutdown(self) -> None:
        """``DockerAgent.shutdown`` must close the shared streamer so in-flight
        reader tasks are cancelled before the underlying Docker client goes
        away."""
        streamer = DockerStatsStreamer(AsyncMock())
        streamer.start("cid_000")
        assert "cid_000" in streamer._tasks

        await streamer.close()

        assert streamer._tasks == {}
        assert streamer._latest == {}

    async def test_stats_streamer_available_before_scan_running_kernels(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Ordering invariant: ``DockerAgent.__ainit__`` must install the shared
        :class:`DockerStatsStreamer` on ``self`` and attach it to the intrinsic
        plugins BEFORE ``super().__ainit__()`` runs.

        ``AbstractAgent.__ainit__`` calls :meth:`scan_running_kernels` and
        starts the container lifecycle handler; on warm restart either of
        those can fire ``_on_container_started`` -> ``self._stats_streamer``
        before any code placed AFTER ``super().__ainit__()`` gets to execute.
        If the streamer is not set by then, ``_on_container_started`` raises
        ``AttributeError`` on a bare class annotation.

        This test monkeypatches :meth:`AbstractAgent.scan_running_kernels`
        (the exact point where the blocker bites) and asserts the streamer
        is already set when it runs. It also confirms the intrinsic plugins
        (discovered via ``hasattr(..., "attach_stats_streamer")``) received
        the same streamer instance before the super init is reached.
        """
        observed_streamer: list[DockerStatsStreamer | None] = []
        observed_cpu_streamer: list[DockerStatsStreamer | None] = []
        observed_mem_streamer: list[DockerStatsStreamer | None] = []

        class _StopAfterOrderingAssertion(BaseException):
            """Sentinel used to short-circuit ``__ainit__`` once the ordering
            invariant has been verified. A ``BaseException`` subclass ensures
            it propagates past any ``except Exception:`` guards in the init
            flow below the stubbed ``super().__ainit__()`` call."""

        cpu_plugin = CPUPlugin.__new__(CPUPlugin)
        mem_plugin = MemoryPlugin.__new__(MemoryPlugin)
        # A non-intrinsic plugin with no attach_stats_streamer attribute
        # must be skipped silently by the hasattr-based attach loop.
        unrelated_plugin = object()

        computer_ctx_cpu = MagicMock()
        computer_ctx_cpu.instance = cpu_plugin
        computer_ctx_mem = MagicMock()
        computer_ctx_mem.instance = mem_plugin
        computer_ctx_other = MagicMock()
        computer_ctx_other.instance = unrelated_plugin

        async def fake_scan_running_kernels(self: Any) -> None:
            # Record the streamer state at the exact moment the race would
            # bite on warm restart.
            observed_streamer.append(getattr(self, "_stats_streamer", None))
            observed_cpu_streamer.append(getattr(cpu_plugin, "_stats_streamer", None))
            observed_mem_streamer.append(getattr(mem_plugin, "_stats_streamer", None))

        async def fake_super_ainit(self: Any) -> None:
            # Emulate the part of AbstractAgent.__ainit__ that matters for
            # this ordering test: call scan_running_kernels, which is where
            # the blocker actually fires on warm restart. Then bail out
            # so the post-super section (which depends on ``self.id``,
            # Redis, networks, etc.) is not exercised.
            await self.scan_running_kernels()
            raise _StopAfterOrderingAssertion()

        # Patch the exact targets of the race.
        monkeypatch.setattr(
            AbstractAgent,
            "scan_running_kernels",
            fake_scan_running_kernels,
            raising=True,
        )
        monkeypatch.setattr(
            AbstractAgent,
            "__ainit__",
            fake_super_ainit,
            raising=True,
        )

        # Stub the pre-super Docker interactions so __ainit__ does not
        # require a live Docker daemon. Only the ordering is under test.
        mock_docker_client = AsyncMock()
        mock_docker_client.version = AsyncMock(
            return_value={"Version": "0", "ApiVersion": "0", "KernelVersion": "test"},
        )
        mock_docker_client.system = MagicMock()
        mock_docker_client.system.info = AsyncMock(return_value={"CgroupDriver": "cgroupfs"})
        mock_docker_client.connector = aiohttp.UnixConnector(path="/var/run/docker.sock")

        def docker_factory(*args: Any, **kwargs: Any) -> AsyncMock:
            return mock_docker_client

        monkeypatch.setattr(
            "ai.backend.agent.docker.agent.Docker",
            docker_factory,
        )

        # ``async with closing_async(Docker()) as docker`` is used in the
        # pre-super section; wrap the mock in an async context manager.
        class _AsyncCMWrapper:
            def __init__(self, obj: Any) -> None:
                self._obj = obj

            async def __aenter__(self) -> Any:
                return self._obj

            async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
                return None

        monkeypatch.setattr(
            "ai.backend.agent.docker.agent.closing_async",
            lambda obj: _AsyncCMWrapper(obj),
        )

        # Construct a minimally-initialised DockerAgent without running
        # the heavy synchronous __init__ (which needs real etcd, registries,
        # etc.). Only the attributes touched before super().__ainit__() need
        # to be populated.
        agent = DockerAgent.__new__(DockerAgent)
        agent.local_config = MagicMock()
        agent.local_config.agent.docker_mode = "native"
        agent._kernel_recovery_adapter = MagicMock()
        agent._kernel_recovery_adapter.adapt_recovery_data = AsyncMock(return_value=None)
        # Typed as ``Mapping[DeviceName, ComputerContext]`` in AbstractAgent;
        # the test uses ``MagicMock`` stand-ins so the attach loop can iterate.
        fake_computers: Any = {
            "cpu": computer_ctx_cpu,
            "mem": computer_ctx_mem,
            "other": computer_ctx_other,
        }
        agent.computers = fake_computers

        with pytest.raises(_StopAfterOrderingAssertion):
            await agent.__ainit__()

        # The patched scan_running_kernels ran exactly once (via the stub
        # super) and at that moment the streamer must already be set.
        assert len(observed_streamer) == 1
        assert observed_streamer[0] is not None
        assert isinstance(observed_streamer[0], DockerStatsStreamer)
        # Both intrinsic plugins must already hold the same streamer instance.
        assert observed_cpu_streamer[0] is observed_streamer[0]
        assert observed_mem_streamer[0] is observed_streamer[0]
        # Non-intrinsic plugins are silently skipped by the hasattr loop.
        assert not hasattr(unrelated_plugin, "_stats_streamer")

        await agent._stats_streamer.close()


def aiohttp_client_connection_error(msg: str) -> Exception:
    """Build a ClientConnectionError without requiring aiohttp internals."""
    return aiohttp.ClientConnectionError(msg)
