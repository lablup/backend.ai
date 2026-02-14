from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.orchestration.idle_checker import (
    IdleCheckerHostDependency,
    IdleCheckerInput,
)


class TestIdleCheckerHostDependency:
    """Test IdleCheckerHostDependency lifecycle."""

    def test_stage_name(self) -> None:
        """Dependency should have correct stage name."""
        dependency = IdleCheckerHostDependency()
        assert dependency.stage_name == "idle-checker-host"

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.idle_checker.init_idle_checkers")
    async def test_provide_starts_and_yields_checker_host(
        self,
        mock_init: AsyncMock,
    ) -> None:
        """Dependency should initialize, start, and yield idle checker host."""
        mock_checker_host = AsyncMock()
        mock_init.return_value = mock_checker_host

        dependency = IdleCheckerHostDependency()
        checker_input = IdleCheckerInput(
            db=MagicMock(),
            config_provider=MagicMock(),
            event_producer=MagicMock(),
            lock_factory=MagicMock(),
        )

        async with dependency.provide(checker_input) as checker_host:
            assert checker_host is mock_checker_host
            mock_init.assert_called_once_with(
                checker_input.db,
                checker_input.config_provider,
                checker_input.event_producer,
                checker_input.lock_factory,
            )
            mock_checker_host.start.assert_awaited_once()

        mock_checker_host.shutdown.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.idle_checker.init_idle_checkers")
    async def test_provide_shuts_down_on_error(
        self,
        mock_init: AsyncMock,
    ) -> None:
        """Dependency should shut down checker host even on error."""
        mock_checker_host = AsyncMock()
        mock_init.return_value = mock_checker_host

        dependency = IdleCheckerHostDependency()
        checker_input = IdleCheckerInput(
            db=MagicMock(),
            config_provider=MagicMock(),
            event_producer=MagicMock(),
            lock_factory=MagicMock(),
        )

        with pytest.raises(RuntimeError, match="test error"):
            async with dependency.provide(checker_input):
                raise RuntimeError("test error")

        mock_checker_host.shutdown.assert_awaited_once()
