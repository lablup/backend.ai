"""
Stage-based setup system with dependency management.

Dependency Graph:
================

Group 0 (Independent - can run concurrently):
    - event_hub
    - redis
    - storage_manager
    - manager_status
    - services

Group 1 (First level dependencies - can run concurrently within group):
    - message_queue (depends on: redis)
    - repositories (depends on: redis, storage_manager)

Group 2 (Second level dependencies):
    - event_producer (depends on: message_queue)
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.setup.provisioners.event_hub import (
    EventHubProvisioner,
    EventHubSpecGenerator,
    EventHubStage,
)
from ai.backend.manager.setup.provisioners.event_producer import (
    EventProducerProvisioner,
    EventProducerSpecGenerator,
    EventProducerStage,
)
from ai.backend.manager.setup.provisioners.manager_status import (
    ManagerStatusProvisioner,
    ManagerStatusSpecGenerator,
    ManagerStatusStage,
)
from ai.backend.manager.setup.provisioners.message_queue import (
    MessageQueueProvisioner,
    MessageQueueSpecGenerator,
    MessageQueueStage,
)
from ai.backend.manager.setup.provisioners.redis import (
    RedisProvisioner,
    RedisSpecGenerator,
    RedisStage,
)
from ai.backend.manager.setup.provisioners.repositories import (
    RepositoriesProvisioner,
    RepositoriesSpecGenerator,
    RepositoriesStage,
)
from ai.backend.manager.setup.provisioners.services import (
    ServicesProvisioner,
    ServicesSpecGenerator,
    ServicesStage,
)
from ai.backend.manager.setup.provisioners.storage_manager import (
    StorageManagerProvisioner,
    StorageManagerSpecGenerator,
    StorageManagerStage,
)


@dataclass
class IndependentStages:
    """Group 0: Stages with no dependencies - can be initialized concurrently"""

    event_hub: EventHubStage
    redis: RedisStage
    storage_manager: StorageManagerStage
    manager_status: ManagerStatusStage
    services: ServicesStage


@dataclass
class FirstDependentStages:
    """Group 1: Stages that depend only on Group 0 stages"""

    message_queue: MessageQueueStage  # depends on: redis
    repositories: RepositoriesStage  # depends on: redis, storage_manager


@dataclass
class SecondDependentStages:
    """Group 2: Stages that depend on Group 1 stages"""

    event_producer: EventProducerStage  # depends on: message_queue


@dataclass
class SetupStageGroup:
    """Complete stage group with all dependency levels"""

    # Group 0: Independent stages
    independent: IndependentStages

    # Group 1: First level dependencies
    first_dependent: FirstDependentStages

    # Group 2: Second level dependencies
    second_dependent: SecondDependentStages

    # Convenience properties for direct access
    @property
    def event_hub(self) -> EventHubStage:
        return self.independent.event_hub

    @property
    def redis(self) -> RedisStage:
        return self.independent.redis

    @property
    def storage_manager(self) -> StorageManagerStage:
        return self.independent.storage_manager

    @property
    def manager_status(self) -> ManagerStatusStage:
        return self.independent.manager_status

    @property
    def services(self) -> ServicesStage:
        return self.independent.services

    @property
    def message_queue(self) -> MessageQueueStage:
        return self.first_dependent.message_queue

    @property
    def repositories(self) -> RepositoriesStage:
        return self.first_dependent.repositories

    @property
    def event_producer(self) -> EventProducerStage:
        return self.second_dependent.event_producer


def create_setup_stages(
    config: ManagerUnifiedConfig,
    db: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    etcd: AsyncEtcd,
    pidx: int = 0,
) -> SetupStageGroup:
    """
    Create stage group with proper dependency handling using SpecGenerators.

    Dependency graph:
    - Group 0 (Independent): event_hub, redis, storage_manager, manager_status, services
    - Group 1 (First dependent):
        - message_queue depends on: redis
        - repositories depends on: redis, storage_manager
    - Group 2 (Second dependent):
        - event_producer depends on: message_queue
    """

    # Group 0: Independent stages (no dependencies)
    independent_stages = IndependentStages(
        event_hub=EventHubStage(EventHubProvisioner()),
        redis=RedisStage(RedisProvisioner()),
        storage_manager=StorageManagerStage(StorageManagerProvisioner()),
        manager_status=ManagerStatusStage(ManagerStatusProvisioner()),
        services=ServicesStage(ServicesProvisioner()),
    )

    # Group 1: First level dependent stages
    first_dependent_stages = FirstDependentStages(
        message_queue=MessageQueueStage(MessageQueueProvisioner()),
        repositories=RepositoriesStage(RepositoriesProvisioner()),
    )

    # Group 2: Second level dependent stages
    second_dependent_stages = SecondDependentStages(
        event_producer=EventProducerStage(EventProducerProvisioner()),
    )

    return SetupStageGroup(
        independent=independent_stages,
        first_dependent=first_dependent_stages,
        second_dependent=second_dependent_stages,
    )


async def setup_all_stages(
    stage_group: SetupStageGroup,
    config: ManagerUnifiedConfig,
    db: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    etcd: AsyncEtcd,
    pidx: int = 0,
) -> Dict[str, Any]:
    """
    Setup all stages concurrently where possible, respecting dependencies.

    Returns a dictionary mapping stage names to their provisioned resources.
    """
    results = {}

    # Group 0: Setup independent stages (can run concurrently)
    await asyncio.gather(
        stage_group.independent.event_hub.setup(EventHubSpecGenerator()),
        stage_group.independent.redis.setup(RedisSpecGenerator(config)),
        stage_group.independent.storage_manager.setup(StorageManagerSpecGenerator(config)),
        stage_group.independent.manager_status.setup(
            ManagerStatusSpecGenerator(pidx, config_provider)
        ),
        stage_group.independent.services.setup(ServicesSpecGenerator(db)),
        return_exceptions=False,
    )

    # Group 1: Setup first level dependent stages (can run concurrently within group)
    await asyncio.gather(
        stage_group.first_dependent.message_queue.setup(
            MessageQueueSpecGenerator(stage_group.independent.redis, config)
        ),
        stage_group.first_dependent.repositories.setup(
            RepositoriesSpecGenerator(
                stage_group.independent.redis,
                stage_group.independent.storage_manager,
                db,
                config_provider,
            )
        ),
        return_exceptions=False,
    )

    # Group 2: Setup second level dependent stages
    await stage_group.second_dependent.event_producer.setup(
        EventProducerSpecGenerator(stage_group.first_dependent.message_queue, config)
    )

    # Collect results from all groups
    results = {
        # Group 0: Independent stages
        "event_hub": await stage_group.independent.event_hub.wait_for_resource(),
        "redis": await stage_group.independent.redis.wait_for_resource(),
        "storage_manager": await stage_group.independent.storage_manager.wait_for_resource(),
        "manager_status": await stage_group.independent.manager_status.wait_for_resource(),
        "services": await stage_group.independent.services.wait_for_resource(),
        # Group 1: First dependent stages
        "message_queue": await stage_group.first_dependent.message_queue.wait_for_resource(),
        "repositories": await stage_group.first_dependent.repositories.wait_for_resource(),
        # Group 2: Second dependent stages
        "event_producer": await stage_group.second_dependent.event_producer.wait_for_resource(),
    }

    return results


async def teardown_all_stages(stage_group: SetupStageGroup) -> None:
    """
    Teardown all stages in reverse dependency order.
    """
    # Group 2: Teardown second level dependent stages first
    await stage_group.second_dependent.event_producer.teardown()

    # Group 1: Teardown first level dependent stages (can run concurrently within group)
    await asyncio.gather(
        stage_group.first_dependent.message_queue.teardown(),
        stage_group.first_dependent.repositories.teardown(),
        return_exceptions=True,
    )

    # Group 0: Teardown independent stages (can run concurrently)
    await asyncio.gather(
        stage_group.independent.event_hub.teardown(),
        stage_group.independent.redis.teardown(),
        stage_group.independent.storage_manager.teardown(),
        stage_group.independent.manager_status.teardown(),
        stage_group.independent.services.teardown(),
        return_exceptions=True,
    )
