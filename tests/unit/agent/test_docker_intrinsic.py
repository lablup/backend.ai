from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Generator, Iterator
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.docker.intrinsic import CPUPlugin, MemoryPlugin, netstat_ns_work
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
            "NetworkSettings": {"SandboxKey": "/var/run/docker/netns/fake"},
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
                "ai.backend.agent.docker.intrinsic.netstat_ns",
                return_value={},
            ),
            patch(
                "ai.backend.agent.docker.intrinsic.current_loop",
            ) as mock_loop,
            patch(
                "asyncio.to_thread",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            mock_container_instance = AsyncMock()
            mock_container_instance.show.return_value = mock_container_data
            mock_container_cls.return_value = mock_container_instance
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=0)
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
        """Even in CGROUP mode, Docker is needed for SandboxKey. Verify instance client is used."""
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            await memory_plugin.gather_container_measures(memory_cgroup_context, container_ids)
            mock_docker_cls.assert_not_called()


class TestMemoryPluginNamespaceValidation(BaseDockerIntrinsicTest):
    """Tests for namespace path pre-validation before netstat_ns call."""

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
        sandbox_key: str | None,
        *,
        ns_path_exists: bool = False,
    ) -> Generator[tuple[MagicMock, MagicMock], None, None]:
        """Build a CGROUP stat context with configurable sandbox_key and path existence."""
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
            "NetworkSettings": {"SandboxKey": sandbox_key},
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
                "ai.backend.agent.docker.intrinsic.netstat_ns",
                new_callable=AsyncMock,
            ) as mock_netstat,
            patch(
                "ai.backend.agent.docker.intrinsic.current_loop",
            ) as mock_loop,
            patch(
                "asyncio.to_thread",
                new_callable=AsyncMock,
                return_value=ns_path_exists,
            ),
        ):
            mock_netstat.return_value = {
                "eth0": MagicMock(bytes_recv=4096, bytes_sent=8192),
            }
            mock_container_instance = AsyncMock()
            mock_container_instance.show.return_value = mock_container_data
            mock_container_cls.return_value = mock_container_instance
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=0)
            yield ctx, mock_netstat

    async def test_nonexistent_namespace_path_returns_zero_net_stats(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
    ) -> None:
        """When namespace path does not exist, net stats should be 0 but other stats collected."""
        with self._make_cgroup_context(
            cgroup_stat_context,
            sandbox_key="/var/run/docker/netns/gone",
            ns_path_exists=False,
        ) as (ctx, mock_netstat):
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            mock_netstat.assert_not_called()
            # mem stats should be collected (read_sysfs returns 1048576)
            assert results[0].per_container["cid_001"].value == 1048576
            # net_rx and net_tx should be 0
            assert results[3].per_container["cid_001"].value == 0
            assert results[4].per_container["cid_001"].value == 0

    async def test_empty_sandbox_key_returns_zero_net_stats(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
    ) -> None:
        """When sandbox_key is empty string, net stats should be 0 but other stats collected."""
        with self._make_cgroup_context(
            cgroup_stat_context,
            sandbox_key="",
            ns_path_exists=False,
        ) as (ctx, mock_netstat):
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            mock_netstat.assert_not_called()
            # mem stats should be collected
            assert results[0].per_container["cid_001"].value == 1048576
            # net_rx and net_tx should be 0
            assert results[3].per_container["cid_001"].value == 0
            assert results[4].per_container["cid_001"].value == 0

    async def test_valid_namespace_path_calls_netstat_ns(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
    ) -> None:
        """When namespace path exists, netstat_ns should be called and net stats collected."""
        with self._make_cgroup_context(
            cgroup_stat_context,
            sandbox_key="/var/run/docker/netns/valid",
            ns_path_exists=True,
        ) as (ctx, mock_netstat):
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            mock_netstat.assert_called()
            # mem stats should be collected
            assert results[0].per_container["cid_001"].value == 1048576
            # net_rx and net_tx should have values from mock netstat_ns
            assert results[3].per_container["cid_001"].value == 4096
            assert results[4].per_container["cid_001"].value == 8192


@pytest.mark.skipif(sys.platform != "linux", reason="Network namespaces require Linux")
class TestNetstatNsWork:
    """Tests for netstat_ns_work with real namespace switching."""

    @pytest.fixture
    def netns_process(self) -> Iterator[subprocess.Popen[bytes]]:
        """Spawn a sleep process in a new network namespace via unshare."""
        proc = subprocess.Popen(
            ["unshare", "--net", "sleep", "30"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.3)
        if proc.poll() is not None:
            pytest.skip("unshare --net failed (insufficient privileges)")
        try:
            yield proc
        finally:
            proc.terminate()
            proc.wait()

    def test_netstat_ns_work_reads_isolated_namespace(
        self, netns_process: subprocess.Popen[bytes]
    ) -> None:
        """netstat_ns_work should read counters from the target namespace,
        not from the host."""
        pid = netns_process.pid
        ns_path = Path(f"/proc/{pid}/ns/net")
        with ProcessPoolExecutor(max_workers=1) as pool:
            result = pool.submit(netstat_ns_work, ns_path).result()
        # A fresh network namespace only has loopback with zero counters.
        assert "lo" in result
        lo = result["lo"]
        assert lo.bytes_recv == 0
        assert lo.bytes_sent == 0

    def test_netstat_ns_work_raises_on_invalid_namespace(self) -> None:
        """netstat_ns_work should raise OSError when setns() fails
        on a non-namespace fd (e.g. /dev/null)."""
        with ProcessPoolExecutor(max_workers=1) as pool:
            future = pool.submit(netstat_ns_work, Path("/dev/null"))
            with pytest.raises(OSError):
                future.result()
