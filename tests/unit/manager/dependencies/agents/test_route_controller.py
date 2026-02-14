from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.agents.route_controller import (
    RouteControllerDependency,
    RouteControllerInput,
)


class TestRouteControllerDependency:
    """Test RouteControllerDependency lifecycle."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.agents.route_controller.RouteController",
    )
    async def test_provide_route_controller(
        self,
        mock_controller_class: MagicMock,
    ) -> None:
        """Dependency should create route controller with correct args."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller

        setup_input = RouteControllerInput(
            valkey_schedule=MagicMock(),
        )

        dependency = RouteControllerDependency()
        async with dependency.provide(setup_input) as controller:
            assert controller is mock_controller
            mock_controller_class.assert_called_once()
