from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.docker.intrinsic import CPUPlugin, MemoryPlugin
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

    async def test_init_creates_docker_client(self) -> None:
        """Verify init() creates a Docker client instance."""
        plugin = CPUPlugin.__new__(CPUPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            mock_docker_cls.return_value = AsyncMock()
            await plugin.init()
            mock_docker_cls.assert_called_once()
            assert plugin._docker is not None

    async def test_cleanup_closes_docker_client(self) -> None:
        """Verify cleanup() closes the Docker client."""
        plugin = CPUPlugin.__new__(CPUPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
        await plugin.cleanup()
        plugin._docker.close.assert_called_once()

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
        ):
            mock_container_instance = AsyncMock()
            mock_container_instance.show.return_value = mock_container_data
            mock_container_cls.return_value = mock_container_instance
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=0)
            yield ctx

    async def test_init_creates_docker_client(self) -> None:
        """Verify init() creates a Docker client instance."""
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        with patch("ai.backend.agent.docker.intrinsic.Docker") as mock_docker_cls:
            mock_docker_cls.return_value = AsyncMock()
            await plugin.init()
            mock_docker_cls.assert_called_once()
            assert plugin._docker is not None

    async def test_cleanup_closes_docker_client(self) -> None:
        """Verify cleanup() closes the Docker client."""
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        plugin._docker = AsyncMock()
        await plugin.cleanup()
        plugin._docker.close.assert_called_once()

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
