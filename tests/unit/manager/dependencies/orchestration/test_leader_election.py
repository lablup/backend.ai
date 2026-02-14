from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.orchestration.leader_election import (
    LeaderElectionDependency,
    LeaderElectionInput,
)


class TestLeaderElectionDependency:
    """Test LeaderElectionDependency lifecycle."""

    def test_stage_name(self) -> None:
        """Dependency should have correct stage name."""
        dependency = LeaderElectionDependency()
        assert dependency.stage_name == "leader-election"

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.ValkeyLeaderClient")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.ValkeyLeaderElection")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.LeaderCron")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.EventProducerTask")
    async def test_provide_starts_and_yields_election(
        self,
        mock_event_producer_task: MagicMock,
        mock_leader_cron_class: MagicMock,
        mock_election_class: MagicMock,
        mock_leader_client_class: MagicMock,
    ) -> None:
        """Dependency should create, configure, start, and yield leader election."""
        # Setup mocks
        mock_client = AsyncMock()
        mock_leader_client_class.create = AsyncMock(return_value=mock_client)

        mock_election = AsyncMock()
        mock_election_class.return_value = mock_election

        mock_orchestrator = MagicMock()
        mock_task_specs = [MagicMock(), MagicMock()]
        mock_orchestrator.create_task_specs.return_value = mock_task_specs

        mock_config_provider = MagicMock()
        mock_config_provider.config.reservoir = None

        mock_event_producer = MagicMock()
        mock_valkey_profile_target = MagicMock()

        dependency = LeaderElectionDependency()
        election_input = LeaderElectionInput(
            valkey_profile_target=mock_valkey_profile_target,
            pidx=0,
            config_provider=mock_config_provider,
            event_producer=mock_event_producer,
            sokovan_orchestrator=mock_orchestrator,
        )

        async with dependency.provide(election_input) as election:
            assert election is mock_election
            mock_leader_client_class.create.assert_awaited_once()
            mock_election.register_task.assert_called_once()
            mock_election.start.assert_awaited_once()

        mock_election.stop.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.ValkeyLeaderClient")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.ValkeyLeaderElection")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.LeaderCron")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.EventProducerTask")
    async def test_provide_adds_reservoir_task_when_enabled(
        self,
        mock_event_producer_task: MagicMock,
        mock_leader_cron_class: MagicMock,
        mock_election_class: MagicMock,
        mock_leader_client_class: MagicMock,
    ) -> None:
        """Dependency should add reservoir scan task when delegation is enabled."""
        mock_client = AsyncMock()
        mock_leader_client_class.create = AsyncMock(return_value=mock_client)

        mock_election = AsyncMock()
        mock_election_class.return_value = mock_election

        mock_orchestrator = MagicMock()
        mock_orchestrator.create_task_specs.return_value = [MagicMock()]

        mock_config_provider = MagicMock()
        mock_config_provider.config.reservoir.use_delegation = True

        dependency = LeaderElectionDependency()
        election_input = LeaderElectionInput(
            valkey_profile_target=MagicMock(),
            pidx=1,
            config_provider=mock_config_provider,
            event_producer=MagicMock(),
            sokovan_orchestrator=mock_orchestrator,
        )

        async with dependency.provide(election_input):
            # Verify that EventProducerTask was called with 2 specs
            # (1 from orchestrator + 1 reservoir scan)
            assert mock_event_producer_task.call_count == 2

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.ValkeyLeaderClient")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.ValkeyLeaderElection")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.LeaderCron")
    @patch("ai.backend.manager.dependencies.orchestration.leader_election.EventProducerTask")
    async def test_provide_stops_on_error(
        self,
        mock_event_producer_task: MagicMock,
        mock_leader_cron_class: MagicMock,
        mock_election_class: MagicMock,
        mock_leader_client_class: MagicMock,
    ) -> None:
        """Dependency should stop leader election even on error."""
        mock_leader_client_class.create = AsyncMock(return_value=AsyncMock())
        mock_election = AsyncMock()
        mock_election_class.return_value = mock_election

        mock_orchestrator = MagicMock()
        mock_orchestrator.create_task_specs.return_value = []

        mock_config_provider = MagicMock()
        mock_config_provider.config.reservoir = None

        dependency = LeaderElectionDependency()
        election_input = LeaderElectionInput(
            valkey_profile_target=MagicMock(),
            pidx=0,
            config_provider=mock_config_provider,
            event_producer=MagicMock(),
            sokovan_orchestrator=mock_orchestrator,
        )

        with pytest.raises(RuntimeError, match="test error"):
            async with dependency.provide(election_input):
                raise RuntimeError("test error")

        mock_election.stop.assert_awaited_once()
