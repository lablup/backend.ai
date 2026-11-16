"""The model card adapter, assembled for one row, with the storage host faked."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentPresetRepository,
)
from ai.backend.manager.repositories.model_card.repository import ModelCardRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.services.deployment_revision_preset.processors import (
    DeploymentPresetProcessors,
)
from ai.backend.manager.services.deployment_revision_preset.service import (
    DeploymentPresetService,
)
from ai.backend.manager.services.model_card.processors import ModelCardProcessors
from ai.backend.manager.services.model_card.service import ModelCardService
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)
from ai.backend.manager.sokovan.deployment.revision_draft.reader import RevisionDraftReader
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)
from bai_scenario.fakes.deployment import FakeValkeyScheduleClient
from bai_scenario.fakes.storage_proxy import (
    FakeStorageProxyManagerFacingClient,
    FakeStorageSessionManager,
)
from bai_scenario.runner.unwired import unwired


@pytest.fixture
def storage() -> FakeStorageProxyManagerFacingClient:
    return FakeStorageProxyManagerFacingClient()


@pytest.fixture
def fakes(storage: FakeStorageProxyManagerFacingClient) -> Sequence[object]:
    """What a ``then`` may read off the outside."""
    return (storage,)


@pytest.fixture
def schedule() -> FakeValkeyScheduleClient:
    return FakeValkeyScheduleClient()


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    storage: FakeStorageProxyManagerFacingClient,
    schedule: FakeValkeyScheduleClient,
) -> ModelCardAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    presets = DeploymentPresetRepository(provider)
    deployments = DeploymentRepository(
        engine,
        ReconcileOpsProvider(engine),
        FakeStorageSessionManager({}),
        unwired(ValkeyStatClient, "only a live deployment reports its usage"),
        unwired(ValkeyLiveClient, "only a live deployment reports its health"),
        unwired(ValkeyScheduleClient, "the controller holds the one that marks work"),
        RbacPermissionCheckRepository(PermissionOpsProvider(engine), config),
    )
    controller = DeploymentController(
        DeploymentControllerArgs(
            scheduling_controller=unwired(
                SchedulingController, "a v2 revision is validated without it"
            ),
            deployment_repository=deployments,
            config_provider=config,
            storage_manager=FakeStorageSessionManager({}),
            event_producer=unwired(EventProducer, "nothing here waits on the event"),
            valkey_schedule=schedule,
            revision_draft_reader=RevisionDraftReader(deployments),
            deployment_revision_preset_repository=presets,
        )
    )
    return ModelCardAdapter(
        ModelCardProcessors(
            registry.group(GroupMeta(ModelCardEntityType())),
            ModelCardService(
                ModelCardRepository(provider),
                FakeStorageSessionManager({"local": storage}),
            ),
        ),
        DeploymentProcessors(
            registry.group(GroupMeta(DeploymentEntityType())),
            DeploymentService(
                controller,
                deployments,
                unwired(AgentRepository, "no deployment here designates an agent"),
                unwired(AppProxyClientPool, "only a served deployment reaches the proxy"),
            ),
        ),
        DeploymentRevisionPresetAdapter(
            DeploymentPresetProcessors(
                registry.group(GroupMeta(DeploymentPresetEntityType())),
                DeploymentPresetService(presets),
            )
        ),
    )
