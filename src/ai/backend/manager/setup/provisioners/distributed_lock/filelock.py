from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.lock import FileLock
from ai.backend.common.stage.types import Provisioner, SpecGenerator
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class FileLockSpec:
    ipc_base_path: Path
    manager_id: str


class FileLockProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "filelock-provisioner"

    @override
    async def setup(self, spec: FileLockSpec) -> DistributedLockFactory:
        return lambda lock_id, lifetime_hint: FileLock(
            spec.ipc_base_path / f"{spec.manager_id}.{lock_id}.lock",
            timeout=0,
        )

    @override
    async def teardown(self, resource: DistributedLockFactory) -> None:
        # Nothing to clean up
        pass


class FileLockSpecGenerator(SpecGenerator[FileLockSpec]):
    def __init__(self, config: ManagerUnifiedConfig):
        self.config = config

    @override
    async def wait_for_spec(self) -> FileLockSpec:
        return FileLockSpec(
            ipc_base_path=self.config.manager.ipc_base_path, manager_id=self.config.manager.id
        )
