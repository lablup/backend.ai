from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.unified import ManagerUnifiedConfig


@dataclass
class StorageManagerSpec:
    config: ManagerUnifiedConfig


class StorageManagerProvisioner(Provisioner[StorageManagerSpec, StorageSessionManager]):
    @property
    def name(self) -> str:
        return "storage_manager"

    async def setup(self, spec: StorageManagerSpec) -> StorageSessionManager:
        # Create the storage session manager with volumes configuration
        storage_manager = StorageSessionManager(spec.config.volumes)
        return storage_manager

    async def teardown(self, resource: StorageSessionManager) -> None:
        # Close all HTTP sessions and clean up resources
        await resource.aclose()
