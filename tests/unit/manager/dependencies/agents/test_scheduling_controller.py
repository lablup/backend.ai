from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.agents.scheduling_controller import (
    SchedulingControllerDependency,
    SchedulingControllerInput,
)


class TestSchedulingControllerDependency:
    """Test SchedulingControllerDependency lifecycle."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.agents.scheduling_controller.SchedulingController",
    )
    async def test_provide_scheduling_controller(
        self,
        mock_controller_class: MagicMock,
    ) -> None:
        """Dependency should create scheduling controller with correct args."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller

        setup_input = SchedulingControllerInput(
            repository=MagicMock(),
            config_provider=MagicMock(),
            storage_manager=MagicMock(),
            event_producer=MagicMock(),
            valkey_schedule=MagicMock(),
            network_plugin_ctx=MagicMock(),
            hook_plugin_ctx=MagicMock(),
        )

        dependency = SchedulingControllerDependency()
        async with dependency.provide(setup_input) as controller:
            assert controller is mock_controller
            mock_controller_class.assert_called_once()
