from __future__ import annotations

import logging
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_leader.client import ValkeyLeaderClient
from ai.backend.common.defs import REDIS_STREAM_LOCK, RedisRole
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact_registry.anycast import (
    DoScanReservoirRegistryEvent,
)
from ai.backend.common.leader import ValkeyLeaderElection, ValkeyLeaderElectionConfig
from ai.backend.common.leader.tasks import EventProducerTask, LeaderCron, PeriodicTask
from ai.backend.common.leader.tasks.event_task import EventTaskSpec
from ai.backend.common.types import ValkeyProfileTarget
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.sokovan.sokovan import SokovanOrchestrator

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class LeaderElectionInput:
    """Input required for leader election setup."""

    valkey_profile_target: ValkeyProfileTarget
    pidx: int
    config_provider: ManagerConfigProvider
    event_producer: EventProducer
    sokovan_orchestrator: SokovanOrchestrator


class LeaderElectionDependency(
    NonMonitorableDependencyProvider[LeaderElectionInput, ValkeyLeaderElection]
):
    """Provides ValkeyLeaderElection lifecycle management.

    Wraps the leader election initialization from the original
    ``leader_election_ctx`` in server.py. Creates leader client,
    configures election, collects task specs, and manages the
    election lifecycle.
    """

    @property
    def stage_name(self) -> str:
        return "leader-election"

    @asynccontextmanager
    async def provide(
        self, setup_input: LeaderElectionInput
    ) -> AsyncIterator[ValkeyLeaderElection]:
        """Initialize and provide leader election.

        Args:
            setup_input: Input containing valkey target, config, event producer,
                and sokovan orchestrator for task spec collection

        Yields:
            Started ValkeyLeaderElection instance
        """
        # Create ValkeyLeaderClient for leader election
        valkey_leader_client = await ValkeyLeaderClient.create(
            valkey_target=setup_input.valkey_profile_target.profile_target(RedisRole.STREAM),
            db_id=REDIS_STREAM_LOCK,
            human_readable_name="leader",
        )

        # Create leader election configuration
        server_id = f"manager-{socket.gethostname()}-{setup_input.pidx}"
        leader_config = ValkeyLeaderElectionConfig(
            server_id=server_id,
            leader_key="leader:sokovan:scheduler",
            lease_duration=30,
            renewal_interval=10.0,
            failure_threshold=3,
        )

        # Create leader election instance
        leader_election = ValkeyLeaderElection(
            leader_client=valkey_leader_client,
            config=leader_config,
        )

        # Get task specifications from sokovan and register them
        task_specs = setup_input.sokovan_orchestrator.create_task_specs()

        # Rescan reservoir registry periodically
        reservoir_config = setup_input.config_provider.config.reservoir

        if reservoir_config and reservoir_config.use_delegation:
            task_specs.append(
                EventTaskSpec(
                    name="reservoir_registry_scan",
                    event_factory=lambda: DoScanReservoirRegistryEvent(),
                    interval=600,
                    initial_delay=0,
                )
            )

        # Create event producer tasks from specs
        leader_tasks: list[PeriodicTask] = [
            EventProducerTask(spec, setup_input.event_producer) for spec in task_specs
        ]

        # Register tasks with the election system
        leader_cron = LeaderCron(tasks=leader_tasks)
        leader_election.register_task(leader_cron)

        # Start leader election
        await leader_election.start()
        log.info("Leader election started for server {}", server_id)

        try:
            yield leader_election
        finally:
            await leader_election.stop()
