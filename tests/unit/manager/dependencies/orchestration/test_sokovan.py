from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.orchestration.sokovan import (
    SokovanOrchestratorDependency,
    SokovanOrchestratorInput,
)


class TestSokovanOrchestratorDependency:
    """Test SokovanOrchestratorDependency lifecycle."""

    def test_stage_name(self) -> None:
        """Dependency should have correct stage name."""
        dependency = SokovanOrchestratorDependency()
        assert dependency.stage_name == "sokovan-orchestrator"

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.create_coordinator_handlers")
    @patch(
        "ai.backend.manager.dependencies.orchestration.sokovan.create_default_scheduler_components"
    )
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.ScheduleCoordinator")
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.RouteCoordinator")
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.DeploymentCoordinator")
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.ClientPool")
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.SokovanOrchestrator")
    async def test_provide_creates_orchestrator(
        self,
        mock_orchestrator_class: MagicMock,
        mock_client_pool_class: MagicMock,
        mock_deployment_coordinator_class: MagicMock,
        mock_route_coordinator_class: MagicMock,
        mock_schedule_coordinator_class: MagicMock,
        mock_create_components: MagicMock,
        mock_create_handlers: MagicMock,
    ) -> None:
        """Dependency should create and yield sokovan orchestrator."""
        mock_components = MagicMock()
        mock_create_components.return_value = mock_components

        mock_handlers = MagicMock()
        mock_create_handlers.return_value = mock_handlers

        mock_orchestrator = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator

        dependency = SokovanOrchestratorDependency()
        sokovan_input = SokovanOrchestratorInput(
            scheduler_repository=MagicMock(),
            deployment_repository=MagicMock(),
            fair_share_repository=MagicMock(),
            resource_usage_repository=MagicMock(),
            config_provider=MagicMock(),
            agent_client_pool=MagicMock(),
            network_plugin_ctx=MagicMock(),
            event_producer=MagicMock(),
            valkey_schedule=MagicMock(),
            valkey_stat=MagicMock(),
            scheduling_controller=MagicMock(),
            deployment_controller=MagicMock(),
            route_controller=MagicMock(),
            distributed_lock_factory=MagicMock(),
            service_discovery=MagicMock(),
        )

        async with dependency.provide(sokovan_input) as orchestrator:
            assert orchestrator is mock_orchestrator
            mock_create_components.assert_called_once()
            mock_create_handlers.assert_called_once()
            mock_orchestrator_class.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.create_coordinator_handlers")
    @patch(
        "ai.backend.manager.dependencies.orchestration.sokovan.create_default_scheduler_components"
    )
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.ScheduleCoordinator")
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.RouteCoordinator")
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.DeploymentCoordinator")
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.ClientPool")
    @patch("ai.backend.manager.dependencies.orchestration.sokovan.SokovanOrchestrator")
    async def test_provide_passes_correct_dependencies(
        self,
        mock_orchestrator_class: MagicMock,
        mock_client_pool_class: MagicMock,
        mock_deployment_coordinator_class: MagicMock,
        mock_route_coordinator_class: MagicMock,
        mock_schedule_coordinator_class: MagicMock,
        mock_create_components: MagicMock,
        mock_create_handlers: MagicMock,
    ) -> None:
        """Dependency should pass correct arguments to scheduler components factory."""
        mock_components = MagicMock()
        mock_create_components.return_value = mock_components
        mock_create_handlers.return_value = MagicMock()
        mock_orchestrator_class.return_value = MagicMock()

        scheduler_repo = MagicMock()
        deployment_repo = MagicMock()
        fair_share_repo = MagicMock()
        config_provider = MagicMock()
        agent_client_pool = MagicMock()
        network_plugin_ctx = MagicMock()
        event_producer = MagicMock()
        valkey_schedule = MagicMock()

        dependency = SokovanOrchestratorDependency()
        sokovan_input = SokovanOrchestratorInput(
            scheduler_repository=scheduler_repo,
            deployment_repository=deployment_repo,
            fair_share_repository=fair_share_repo,
            resource_usage_repository=MagicMock(),
            config_provider=config_provider,
            agent_client_pool=agent_client_pool,
            network_plugin_ctx=network_plugin_ctx,
            event_producer=event_producer,
            valkey_schedule=valkey_schedule,
            valkey_stat=MagicMock(),
            scheduling_controller=MagicMock(),
            deployment_controller=MagicMock(),
            route_controller=MagicMock(),
            distributed_lock_factory=MagicMock(),
            service_discovery=MagicMock(),
        )

        async with dependency.provide(sokovan_input):
            mock_create_components.assert_called_once_with(
                scheduler_repo,
                deployment_repo,
                fair_share_repo,
                config_provider,
                agent_client_pool,
                network_plugin_ctx,
                event_producer,
                valkey_schedule,
            )
