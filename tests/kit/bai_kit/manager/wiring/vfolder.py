"""VFolder wiring: the vfolder processors plus the storage-proxy fake as its extra."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.vfolder import VFOLDER_ENTITY_TYPE
from ai.backend.common.dto.manager.v2.vfolder.request import CreateVFolderInput
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
from bai_kit.manager.fakes.storage_proxy import (
    FakeStorageProxyManagerFacingClient,
    FakeStorageSessionManager,
    StorageScript,
)
from bai_kit.manager.runner import Wired, WiringDeps

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors  # pants: no-infer-dep


@dataclass
class VFolderAdapterProcessors:
    vfolder: VFolderProcessors


DISPATCH: dict[type, str] = {
    CreateVFolderInput: "create",
    # get(vfolder_id) / delete(vfolder_id) take an id, not a DTO: Call("get", id).
}

STORAGE_EXTRA = "storage"


def _storage_client(extra: Any) -> StorageProxyManagerFacingClient:
    """``Setup.extras["storage"]`` may be a script (alternative 1), a fake subclass
    (alternative 2), a ready instance, or absent."""
    if extra is None:
        return FakeStorageProxyManagerFacingClient()
    if isinstance(extra, StorageScript):
        return FakeStorageProxyManagerFacingClient(extra)
    if isinstance(extra, type):
        return cast(StorageProxyManagerFacingClient, extra())
    return cast(StorageProxyManagerFacingClient, extra)


def vfolder_wiring(deps: WiringDeps) -> Wired:
    storage = _storage_client(deps.extras.get(STORAGE_EXTRA))
    provider = V2DBOpsProvider(deps.engine)
    share_provider = ShareOpsProvider(deps.engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=deps.monitors,
            validators=deps.v2_validators,
            repository=OpsRepository(provider),
        )
    )
    service = VFolderService(
        config_provider=deps.config_provider,
        etcd=MagicMock(spec=AsyncEtcd),
        storage_manager=FakeStorageSessionManager({"local": storage}),
        background_task_manager=MagicMock(spec=BackgroundTaskManager),
        vfolder_repository=VfolderRepository(deps.engine, share_provider),
        user_repository=UserRepository(
            deps.engine,
            provider,
            share_provider,
            KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
        ),
        valkey_stat_client=MagicMock(spec=ValkeyStatClient),
    )
    processors = VFolderProcessors(registry.group(GroupMeta(VFOLDER_ENTITY_TYPE)), service)
    adapter = VFolderAdapter(cast("Processors", VFolderAdapterProcessors(processors)))
    return Wired(
        adapter=adapter,
        dispatch=DISPATCH,
        client_attr="vfolder",
        extras={STORAGE_EXTRA: storage},
    )
