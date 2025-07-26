from dataclasses import dataclass
from typing import override

from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.unified import VolumesConfig

from ..models.storage import StorageSessionManager


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
