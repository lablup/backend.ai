from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.common.dependencies.stacks.builder import DependencyBuilderStack
from ai.backend.manager.dependencies.orchestration.composer import (
    OrchestrationComposer,
    OrchestrationInput,
)


class TestOrchestrationComposer:
    """Test OrchestrationComposer composition."""

    def test_stage_name(self) -> None:
        """Composer should have correct stage name."""
        composer = OrchestrationComposer()
        assert composer.stage_name == "orchestration"

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.composer.LeaderElectionDependency")
    @patch("ai.backend.manager.dependencies.orchestration.composer.SokovanOrchestratorDependency")
    @patch("ai.backend.manager.dependencies.orchestration.composer.IdleCheckerHostDependency")
    async def test_compose_creates_all_resources(
        self,
        mock_idle_checker_dep_class: MagicMock,
        mock_sokovan_dep_class: MagicMock,
        mock_leader_dep_class: MagicMock,
    ) -> None:
        """Composer should create all three orchestration resources."""
        mock_idle_checker_dep_class.return_value = MagicMock()
        mock_sokovan_dep_class.return_value = MagicMock()
        mock_leader_dep_class.return_value = MagicMock()

        composer = OrchestrationComposer()
        orchestration_input = OrchestrationInput(
            db=MagicMock(),
            config_provider=MagicMock(),
            event_producer=MagicMock(),
            distributed_lock_factory=MagicMock(),
            valkey_profile_target=MagicMock(),
            valkey_schedule=MagicMock(),
            valkey_stat=MagicMock(),
            pidx=0,
            scheduler_repository=MagicMock(),
            deployment_repository=MagicMock(),
            fair_share_repository=MagicMock(),
            resource_usage_repository=MagicMock(),
            agent_client_pool=MagicMock(),
            network_plugin_ctx=MagicMock(),
            scheduling_controller=MagicMock(),
            deployment_controller=MagicMock(),
            route_controller=MagicMock(),
            service_discovery=MagicMock(),
        )

        async with DependencyBuilderStack() as stack:
            async with composer.compose(stack, orchestration_input) as resources:
                assert resources.idle_checker_host is not None
                assert resources.sokovan_orchestrator is not None
                assert resources.leader_election is not None

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.composer.LeaderElectionDependency")
    @patch("ai.backend.manager.dependencies.orchestration.composer.SokovanOrchestratorDependency")
    @patch("ai.backend.manager.dependencies.orchestration.composer.IdleCheckerHostDependency")
    async def test_compose_initializes_dependencies_in_order(
        self,
        mock_idle_checker_dep_class: MagicMock,
        mock_sokovan_dep_class: MagicMock,
        mock_leader_dep_class: MagicMock,
    ) -> None:
        """Composer should initialize dependencies in the correct order."""
        call_order: list[str] = []

        mock_idle_checker_dep = MagicMock()
        mock_sokovan_dep = MagicMock()
        mock_leader_dep = MagicMock()

        mock_idle_checker_dep_class.return_value = mock_idle_checker_dep
        mock_sokovan_dep_class.return_value = mock_sokovan_dep
        mock_leader_dep_class.return_value = mock_leader_dep

        # Track call order through stage_name
        mock_idle_checker_dep.stage_name = "idle-checker-host"
        mock_sokovan_dep.stage_name = "sokovan-orchestrator"
        mock_leader_dep.stage_name = "leader-election"

        mock_idle_checker_dep.gen_health_checkers.return_value = None
        mock_sokovan_dep.gen_health_checkers.return_value = None
        mock_leader_dep.gen_health_checkers.return_value = None

        def make_provide(name: str, result: MagicMock) -> object:
            @asynccontextmanager
            async def _provide(setup_input: object) -> AsyncIterator[MagicMock]:
                call_order.append(name)
                yield result

            return _provide

        mock_idle_result = MagicMock()
        mock_sokovan_result = MagicMock()
        mock_leader_result = MagicMock()

        mock_idle_checker_dep.provide = make_provide("idle-checker", mock_idle_result)
        mock_sokovan_dep.provide = make_provide("sokovan", mock_sokovan_result)
        mock_leader_dep.provide = make_provide("leader", mock_leader_result)

        composer = OrchestrationComposer()
        orchestration_input = OrchestrationInput(
            db=MagicMock(),
            config_provider=MagicMock(),
            event_producer=MagicMock(),
            distributed_lock_factory=MagicMock(),
            valkey_profile_target=MagicMock(),
            valkey_schedule=MagicMock(),
            valkey_stat=MagicMock(),
            pidx=0,
            scheduler_repository=MagicMock(),
            deployment_repository=MagicMock(),
            fair_share_repository=MagicMock(),
            resource_usage_repository=MagicMock(),
            agent_client_pool=MagicMock(),
            network_plugin_ctx=MagicMock(),
            scheduling_controller=MagicMock(),
            deployment_controller=MagicMock(),
            route_controller=MagicMock(),
            service_discovery=MagicMock(),
        )

        async with DependencyBuilderStack() as stack:
            async with composer.compose(stack, orchestration_input) as resources:
                assert call_order == ["idle-checker", "sokovan", "leader"]
                assert resources.idle_checker_host is mock_idle_result
                assert resources.sokovan_orchestrator is mock_sokovan_result
                assert resources.leader_election is mock_leader_result
