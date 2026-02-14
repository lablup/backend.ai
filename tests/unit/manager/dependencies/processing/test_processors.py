from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.processing.processors import (
    ProcessorsDependency,
    ProcessorsProviderInput,
)


class TestProcessorsDependency:
    """Test ProcessorsDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.processing.processors.Processors")
    async def test_provide_processors(
        self,
        mock_processors_class: MagicMock,
    ) -> None:
        """Dependency should create Processors via Processors.create()."""
        mock_processors = MagicMock()
        mock_processors_class.create.return_value = mock_processors

        mock_service_args = MagicMock()
        mock_monitors = [MagicMock(), MagicMock()]

        dependency = ProcessorsDependency()
        processors_input = ProcessorsProviderInput(
            service_args=mock_service_args,
            action_monitors=mock_monitors,
        )

        async with dependency.provide(processors_input) as processors:
            assert processors is mock_processors
            mock_processors_class.create.assert_called_once()
            call_args = mock_processors_class.create.call_args
            assert call_args[0][0].service_args is mock_service_args
            assert call_args[0][1] is mock_monitors
