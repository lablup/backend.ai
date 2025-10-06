from __future__ import annotations

import logging
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_leader.client import ValkeyLeaderClient
from ai.backend.common.defs import REDIS_STREAM_LOCK, RedisRole
from ai.backend.common.events.event_types.artifact_registry.anycast import (
    DoScanReservoirRegistryEvent,
)
from ai.backend.common.leader import ValkeyLeaderElection, ValkeyLeaderElectionConfig
from ai.backend.common.leader.tasks import (
    EventProducerTask,
    EventTaskSpec,
    LeaderCron,
    PeriodicTask,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ..api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@actxmgr
async def leader_election_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Initialize leader election for distributed coordination."""

    # Create ValkeyLeaderClient for leader election
    valkey_leader_client = await ValkeyLeaderClient.create(
        valkey_target=root_ctx.valkey_profile_target.profile_target(RedisRole.STREAM),
        db_id=REDIS_STREAM_LOCK,  # Use a dedicated DB for leader election
        human_readable_name="leader",
    )

    # Create leader election configuration
    server_id = f"manager-{socket.gethostname()}-{root_ctx.pidx}"
    leader_config = ValkeyLeaderElectionConfig(
        server_id=server_id,
        leader_key="leader:sokovan:scheduler",
        lease_duration=30,
        renewal_interval=10.0,
        failure_threshold=3,
    )

    # Create leader election instance
    root_ctx.leader_election = ValkeyLeaderElection(
        leader_client=valkey_leader_client,
        config=leader_config,
    )

    # Get task specifications from sokovan and register them
    task_specs = root_ctx.sokovan_orchestrator.create_task_specs()

    # Rescan reservoir registry periodically
    task_specs.append(
        EventTaskSpec(
            name="reservoir_registry_scan",
            event_factory=lambda: DoScanReservoirRegistryEvent(),
            interval=3600,  # 1 hour
            initial_delay=0,
        )
    )

    # Create event producer tasks from specs
    leader_tasks: list[PeriodicTask] = [
        EventProducerTask(spec, root_ctx.event_producer) for spec in task_specs
    ]

    # Register tasks with the election system
    leader_cron = LeaderCron(tasks=leader_tasks)
    root_ctx.leader_election.register_task(leader_cron)

    # Start leader election (will start tasks when becoming leader)
    await root_ctx.leader_election.start()
    log.info(f"Leader election started for server {server_id}")

    yield

    # Cleanup leader election
    await root_ctx.leader_election.stop()
