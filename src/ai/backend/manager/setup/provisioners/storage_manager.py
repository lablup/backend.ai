from dataclasses import dataclass
from typing import override

from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.manager.config.unified import ManagerUnifiedConfig, VolumesConfig
from ai.backend.manager.models.storage import StorageSessionManager


@dataclass
class StorageManagerSpec:
    volume_config: VolumesConfig


class StorageManagerProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "storage-manager-provisioner"

    @override
    async def setup(self, spec: StorageManagerSpec) -> StorageSessionManager:
        storage_manager = StorageSessionManager(spec.volume_config)
        return storage_manager

    @override
    async def teardown(self, resource: StorageSessionManager) -> None:
        await resource.aclose()


class StorageManagerSpecGenerator(SpecGenerator[StorageManagerSpec]):
    def __init__(self, config: ManagerUnifiedConfig):
        self.config = config

    @override
    async def wait_for_spec(self) -> StorageManagerSpec:
        return StorageManagerSpec(volume_config=self.config.volumes)


# Type alias for StorageManager stage
StorageManagerStage = ProvisionStage[StorageManagerSpec, StorageSessionManager]
