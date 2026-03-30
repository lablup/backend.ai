from __future__ import annotations

from unittest.mock import MagicMock, patch

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.dependencies.processing.processors import (
    ProcessorsDependency,
    ProcessorsProviderInput,
)


class TestProcessorsDependency:
    """Test ProcessorsDependency lifecycle."""

    @patch("ai.backend.manager.dependencies.processing.processors.create_processors")
    async def test_provide_processors(
        self,
        mock_create_processors: MagicMock,
    ) -> None:
        """Dependency should create Processors via create_processors()."""
        mock_processors = MagicMock()
        mock_create_processors.return_value = mock_processors

        mock_service_args = MagicMock()
        mock_monitors: list[ActionMonitor] = [MagicMock(), MagicMock()]

        dependency = ProcessorsDependency()
        processors_input = ProcessorsProviderInput(
            service_args=mock_service_args,
            action_monitors=mock_monitors,
            event_hub=MagicMock(),
            event_fetcher=MagicMock(),
            validators=MagicMock(spec=ActionValidators),
        )

        async with dependency.provide(processors_input) as processors:
            assert processors is mock_processors
            mock_create_processors.assert_called_once()
            call_args = mock_create_processors.call_args
            assert call_args[0][0].service_args is mock_service_args
            assert call_args[0][1] is mock_monitors
