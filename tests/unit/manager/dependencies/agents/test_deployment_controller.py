from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.agents.deployment_controller import (
    DeploymentControllerDependency,
    DeploymentControllerInput,
)


class TestDeploymentControllerDependency:
    """Test DeploymentControllerDependency lifecycle."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.agents.deployment_controller.DeploymentController",
    )
    async def test_provide_deployment_controller(
        self,
        mock_controller_class: MagicMock,
    ) -> None:
        """Dependency should create deployment controller with correct args."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller

        setup_input = DeploymentControllerInput(
            scheduling_controller=MagicMock(),
            deployment_repository=MagicMock(),
            config_provider=MagicMock(),
            storage_manager=MagicMock(),
            event_producer=MagicMock(),
            valkey_schedule=MagicMock(),
            revision_generator_registry=MagicMock(),
        )

        dependency = DeploymentControllerDependency()
        async with dependency.provide(setup_input) as controller:
            assert controller is mock_controller
            mock_controller_class.assert_called_once()
