"""The deployment adapter, assembled for one row.

Two dependencies answer rather than refuse. The schedule client is marked by every
write that hands work to the coordinator, so a row that means to trigger one reads the
mark back. The coordinator is asked which handlers are registered when options are
replaced, so a row that names one reads the name off a real handler.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest
from bai_scenario.fakes.deployment import FakeDeploymentCoordinator, FakeValkeyScheduleClient
from bai_scenario.fakes.storage_proxy import FakeStorageSessionManager
from bai_scenario.runner.unwired import unwired

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.handlers.base import DeploymentHandler
from ai.backend.manager.sokovan.deployment.handlers.deploying_initializing import (
    DeployingInitializingHandler,
)
from ai.backend.manager.sokovan.deployment.handlers.replica import CheckReplicaDeploymentHandler
from ai.backend.manager.sokovan.deployment.revision_draft.reader import RevisionDraftReader
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)


@pytest.fixture
def schedule() -> FakeValkeyScheduleClient:
    return FakeValkeyScheduleClient()


@pytest.fixture
def handlers() -> Sequence[DeploymentHandler]:
    """등록된 처리기. 이름만 읽으므로 안쪽은 배선하지 않는다."""
    executor = unwired(DeploymentExecutor, "처리기의 이름만 읽는다")
    controller = unwired(DeploymentController, "처리기의 이름만 읽는다")
    return (
        CheckReplicaDeploymentHandler(
            deployment_executor=executor, deployment_controller=controller
        ),
        DeployingInitializingHandler(
            deployment_controller=controller, deployment_executor=executor
        ),
    )


@pytest.fixture
def coordinator(handlers: Sequence[DeploymentHandler]) -> FakeDeploymentCoordinator:
    return FakeDeploymentCoordinator(handlers)


@pytest.fixture
def fakes(schedule: FakeValkeyScheduleClient) -> Sequence[object]:
    """What a ``then`` may read off the outside."""
    return (schedule,)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    schedule: FakeValkeyScheduleClient,
    coordinator: FakeDeploymentCoordinator,
) -> DeploymentAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    repository = DeploymentRepository(
        engine,
        ReconcileOpsProvider(engine),
        FakeStorageSessionManager({}),
        unwired(ValkeyStatClient, "only a live deployment reports its usage"),
        unwired(ValkeyLiveClient, "only a live deployment reports its health"),
        unwired(ValkeyScheduleClient, "the controller holds the one that marks work"),
    )
    controller = DeploymentController(
        DeploymentControllerArgs(
            scheduling_controller=unwired(
                SchedulingController, "only a deployment holding a revision validates one"
            ),
            deployment_repository=repository,
            config_provider=config,
            storage_manager=FakeStorageSessionManager({}),
            event_producer=unwired(EventProducer, "nothing here waits on the event"),
            valkey_schedule=schedule,
            revision_draft_reader=unwired(RevisionDraftReader, "only a revision reads a draft"),
            deployment_revision_preset_repository=None,
        )
    )
    service = DeploymentService(
        controller,
        repository,
        unwired(AppProxyClientPool, "only a served deployment reaches the proxy"),
    )
    return DeploymentAdapter(
        DeploymentProcessors(registry.group(GroupMeta(DeploymentEntityType())), service),
        coordinator,
    )
