from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.plugins.monitoring import (
    ErrorMonitorDependency,
    MonitoringInput,
    StatsMonitorDependency,
)


def _make_monitoring_input() -> MonitoringInput:
    return MonitoringInput(
        etcd=MagicMock(),
        local_config={"key": "value"},
        allowed_plugins={"plugin_a"},
        disabled_plugins={"plugin_b"},
        error_log_repository=MagicMock(),
    )


class TestErrorMonitorDependency:
    def test_stage_name(self) -> None:
        dep = ErrorMonitorDependency()
        assert dep.stage_name == "error-monitor-plugin"

    @patch("ai.backend.manager.dependencies.plugins.monitoring.ManagerErrorPluginContext")
    async def test_provide_initializes_and_yields_context(self, mock_ctx_class: MagicMock) -> None:
        monitoring_input = _make_monitoring_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {"error_plugin": MagicMock()}
        mock_ctx_class.return_value = mock_ctx

        dep = ErrorMonitorDependency()

        async with dep.provide(monitoring_input) as ctx:
            assert ctx is mock_ctx
            mock_ctx_class.assert_called_once_with(
                monitoring_input.etcd, monitoring_input.local_config
            )
            mock_ctx.init.assert_called_once_with(
                context={"error_log_repository": monitoring_input.error_log_repository},
                allowlist=monitoring_input.allowed_plugins,
            )

        mock_ctx.cleanup.assert_called_once()

    @patch("ai.backend.manager.dependencies.plugins.monitoring.ManagerErrorPluginContext")
    async def test_propagates_init_failure(self, mock_ctx_class: MagicMock) -> None:
        monitoring_input = _make_monitoring_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock(side_effect=Exception("init failed"))
        mock_ctx.cleanup = AsyncMock()
        mock_ctx_class.return_value = mock_ctx

        dep = ErrorMonitorDependency()

        with pytest.raises(Exception, match="init failed"):
            async with dep.provide(monitoring_input):
                pass

        mock_ctx.cleanup.assert_not_called()

    @patch("ai.backend.manager.dependencies.plugins.monitoring.ManagerErrorPluginContext")
    async def test_cleanup_on_exception(self, mock_ctx_class: MagicMock) -> None:
        monitoring_input = _make_monitoring_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {}
        mock_ctx_class.return_value = mock_ctx

        dep = ErrorMonitorDependency()

        with pytest.raises(RuntimeError):
            async with dep.provide(monitoring_input) as ctx:
                assert ctx is mock_ctx
                raise RuntimeError("Test error")

        mock_ctx.cleanup.assert_called_once()


class TestStatsMonitorDependency:
    def test_stage_name(self) -> None:
        dep = StatsMonitorDependency()
        assert dep.stage_name == "stats-monitor-plugin"

    @patch("ai.backend.manager.dependencies.plugins.monitoring.ManagerStatsPluginContext")
    async def test_provide_initializes_and_yields_context(self, mock_ctx_class: MagicMock) -> None:
        monitoring_input = _make_monitoring_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {"stats_plugin": MagicMock()}
        mock_ctx_class.return_value = mock_ctx

        dep = StatsMonitorDependency()

        async with dep.provide(monitoring_input) as ctx:
            assert ctx is mock_ctx
            mock_ctx_class.assert_called_once_with(
                monitoring_input.etcd, monitoring_input.local_config
            )
            mock_ctx.init.assert_called_once_with(
                allowlist=monitoring_input.allowed_plugins,
            )

        mock_ctx.cleanup.assert_called_once()

    @patch("ai.backend.manager.dependencies.plugins.monitoring.ManagerStatsPluginContext")
    async def test_propagates_init_failure(self, mock_ctx_class: MagicMock) -> None:
        monitoring_input = _make_monitoring_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock(side_effect=Exception("init failed"))
        mock_ctx.cleanup = AsyncMock()
        mock_ctx_class.return_value = mock_ctx

        dep = StatsMonitorDependency()

        with pytest.raises(Exception, match="init failed"):
            async with dep.provide(monitoring_input):
                pass

        mock_ctx.cleanup.assert_not_called()

    @patch("ai.backend.manager.dependencies.plugins.monitoring.ManagerStatsPluginContext")
    async def test_cleanup_on_exception(self, mock_ctx_class: MagicMock) -> None:
        monitoring_input = _make_monitoring_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {}
        mock_ctx_class.return_value = mock_ctx

        dep = StatsMonitorDependency()

        with pytest.raises(RuntimeError):
            async with dep.provide(monitoring_input) as ctx:
                assert ctx is mock_ctx
                raise RuntimeError("Test error")

        mock_ctx.cleanup.assert_called_once()
