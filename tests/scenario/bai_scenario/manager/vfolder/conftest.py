"""The vfolder adapter, assembled for one row, with the storage host faked.

Every processor the adapter holds is real. File operations answer through the fake
storage proxy, admin search through the same vfolder group, mount policies through their
own service, and ``deploy`` through the deployment controller the deployment table uses.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.bulk.validator.rbac import BulkOwnCheck
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentPresetRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.services.vfolder.processors.file import VFolderFileProcessors
from ai.backend.manager.services.vfolder.processors.mount_policy import (
    VFolderMountPolicyProcessors,
)
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.processors.vfolder_admin import VFolderAdminProcessors
from ai.backend.manager.services.vfolder.services.file import VFolderFileService
from ai.backend.manager.services.vfolder.services.mount_policy import VFolderMountPolicyService
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
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
from bai_scenario.valkey import ScenarioValkey


@pytest.fixture
def storage() -> FakeStorageProxyManagerFacingClient:
    return FakeStorageProxyManagerFacingClient()


@pytest.fixture
def schedule() -> FakeValkeyScheduleClient:
    return FakeValkeyScheduleClient()


@pytest.fixture
def fakes(
    storage: FakeStorageProxyManagerFacingClient,
    schedule: FakeValkeyScheduleClient,
) -> Sequence[object]:
    """What a ``then`` may read off the outside."""
    return (storage, schedule)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    storage: FakeStorageProxyManagerFacingClient,
    schedule: FakeValkeyScheduleClient,
    valkey: ScenarioValkey,
) -> VFolderAdapter:
    provider = V2DBOpsProvider(engine)
    share_provider = ShareOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    storage_manager = FakeStorageSessionManager({"local": storage})
    permission_check = RbacPermissionCheckRepository(PermissionOpsProvider(engine), config)
    vfolder_repository = VfolderRepository(engine, share_provider)
    user_repository = UserRepository(
        engine,
        provider,
        share_provider,
        ResourcePolicyOpsProvider(engine),
        KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )
    service = VFolderService(
        config_provider=config,
        etcd=MagicMock(spec=AsyncEtcd),
        storage_manager=storage_manager,
        background_task_manager=MagicMock(spec=BackgroundTaskManager),
        vfolder_repository=vfolder_repository,
        user_repository=user_repository,
        valkey_stat_client=valkey.stat,
        own_check=BulkOwnCheck(permission_check),
    )
    file_service = VFolderFileService(
        config_provider=config,
        storage_manager=storage_manager,
        vfolder_repository=vfolder_repository,
        user_repository=user_repository,
    )
    mount_policy_service = VFolderMountPolicyService(
        vfolder_repository=vfolder_repository,
        permission_check=permission_check,
    )
    preset_repository = DeploymentPresetRepository(provider)
    deployment_repository = DeploymentRepository(
        engine,
        ReconcileOpsProvider(engine),
        storage_manager,
        unwired(ValkeyStatClient, "only a live deployment reports its usage"),
        unwired(ValkeyLiveClient, "only a live deployment reports its health"),
        unwired(ValkeyScheduleClient, "the controller holds the one that marks work"),
        permission_check,
    )
    deployment_controller = DeploymentController(
        DeploymentControllerArgs(
            scheduling_controller=unwired(
                SchedulingController, "only a deployment holding a revision validates one"
            ),
            deployment_repository=deployment_repository,
            config_provider=config,
            storage_manager=storage_manager,
            event_producer=unwired(EventProducer, "nothing here waits on the event"),
            valkey_schedule=schedule,
            revision_draft_reader=RevisionDraftReader(deployment_repository),
            deployment_revision_preset_repository=preset_repository,
        )
    )
    deployment_service = DeploymentService(
        deployment_controller,
        deployment_repository,
        unwired(AgentRepository, "no deployment here designates an agent"),
        unwired(AppProxyClientPool, "only a served deployment reaches the proxy"),
        preset_repository,
    )
    group = registry.group(GroupMeta(VFolderEntityType()))
    return VFolderAdapter(
        VFolderProcessors(group, service),
        VFolderFileProcessors(group, file_service),
        VFolderAdminProcessors(group),
        DeploymentProcessors(registry.group(GroupMeta(DeploymentEntityType())), deployment_service),
        VFolderMountPolicyProcessors(group, mount_policy_service),
    )
