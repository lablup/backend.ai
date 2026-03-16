from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.docker.intrinsic import MemoryPlugin
from ai.backend.agent.stats import StatModes


class TestMemoryPluginNamespaceValidation:
    """Tests for namespace path pre-validation before netstat_ns call."""

    @pytest.fixture
    def memory_plugin(self) -> MemoryPlugin:
        plugin = MemoryPlugin.__new__(MemoryPlugin)
        plugin.local_config = {"agent": {"docker-mode": "default"}}
        return plugin

    @pytest.fixture
    def cgroup_stat_context(self) -> MagicMock:
        ctx = MagicMock()
        ctx.mode = StatModes.CGROUP
        return ctx

    @contextmanager
    def _make_cgroup_context(
        self,
        cgroup_stat_context: MagicMock,
        sandbox_key: str,
    ) -> Generator[tuple[MagicMock, MagicMock], None, None]:
        """Build a CGROUP stat context with configurable sandbox_key."""
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
                "ai.backend.agent.docker.intrinsic.Docker",
            ),
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
                "ai.backend.agent.docker.intrinsic.closing_async",
            ) as mock_closing,
        ):
            mock_netstat.return_value = {
                "eth0": MagicMock(bytes_recv=4096, bytes_sent=8192),
            }
            mock_container_instance = AsyncMock()
            mock_container_instance.show.return_value = mock_container_data
            mock_container_cls.return_value = mock_container_instance

            # Mock closing_async context manager to return mock docker
            mock_docker_instance = AsyncMock()
            mock_closing_cm = AsyncMock()
            mock_closing_cm.__aenter__ = AsyncMock(return_value=mock_docker_instance)
            mock_closing_cm.__aexit__ = AsyncMock(return_value=False)
            mock_closing.return_value = mock_closing_cm

            mock_loop.return_value.run_in_executor = AsyncMock(return_value=0)
            yield ctx, mock_netstat

    async def test_nonexistent_namespace_path_skips_netstat(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
        tmp_path: Path,
    ) -> None:
        """When namespace path does not exist, netstat_ns should not be called."""
        gone_path = tmp_path / "nonexistent_netns"
        with self._make_cgroup_context(
            cgroup_stat_context,
            sandbox_key=str(gone_path),
        ) as (ctx, mock_netstat):
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            mock_netstat.assert_not_called()
            # Results should still be returned (mem stats collected)
            assert results is not None

    async def test_empty_sandbox_key_skips_netstat(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
    ) -> None:
        """When sandbox_key is empty string, netstat_ns should not be called."""
        with self._make_cgroup_context(
            cgroup_stat_context,
            sandbox_key="",
        ) as (ctx, mock_netstat):
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            mock_netstat.assert_not_called()
            assert results is not None

    async def test_valid_namespace_path_calls_netstat_ns(
        self,
        memory_plugin: MemoryPlugin,
        cgroup_stat_context: MagicMock,
        tmp_path: Path,
    ) -> None:
        """When namespace path exists, netstat_ns should be called."""
        valid_path = tmp_path / "valid_netns"
        valid_path.touch()
        with self._make_cgroup_context(
            cgroup_stat_context,
            sandbox_key=str(valid_path),
        ) as (ctx, mock_netstat):
            results = await memory_plugin.gather_container_measures(ctx, ["cid_001"])
            mock_netstat.assert_called()
            assert results is not None
