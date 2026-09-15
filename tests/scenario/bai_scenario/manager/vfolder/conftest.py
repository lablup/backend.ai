"""The vfolder adapter, assembled for one row, with the storage host faked."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from unittest.mock import MagicMock

import pytest
from bai_scenario.fakes.storage_proxy import (
    FakeStorageProxyManagerFacingClient,
    FakeStorageSessionManager,
)
from bai_scenario.runner.unwired import unwired
from bai_scenario.valkey import ScenarioValkey

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.admin_repository import VFolderAdminRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.vfolder.processors.file import VFolderFileProcessors
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.processors.vfolder_admin import VFolderAdminProcessors
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
from ai.backend.manager.services.vfolder.services.vfolder_admin import VFolderAdminService


@pytest.fixture
def storage() -> FakeStorageProxyManagerFacingClient:
    return FakeStorageProxyManagerFacingClient()


@pytest.fixture
def fakes(storage: FakeStorageProxyManagerFacingClient) -> Sequence[object]:
    """What a ``then`` may read off the outside."""
    return (storage,)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    storage: FakeStorageProxyManagerFacingClient,
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
    service = VFolderService(
        config_provider=config,
        etcd=MagicMock(spec=AsyncEtcd),
        storage_manager=FakeStorageSessionManager({"local": storage}),
        background_task_manager=MagicMock(spec=BackgroundTaskManager),
        vfolder_repository=VfolderRepository(engine, share_provider),
        user_repository=UserRepository(
            engine,
            provider,
            share_provider,
            KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
        ),
        valkey_stat_client=valkey.stat,
    )
    return VFolderAdapter(
        VFolderProcessors(registry.group(GroupMeta(VFolderEntityType())), service),
        unwired(VFolderFileProcessors, "no file operation is exercised here"),
        VFolderAdminProcessors(
            registry.group(GroupMeta(VFolderEntityType())),
            VFolderAdminService(VFolderAdminRepository(engine)),
        ),
        unwired(DeploymentProcessors, "only deploy() reaches it"),
    )
