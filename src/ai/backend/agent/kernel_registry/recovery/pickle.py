from dataclasses import dataclass
from pathlib import Path

from ...kernel import KernelRegistry
from ..loader.pickle import PickleBasedKernelRegistryLoader
from ..writer.pickle import PickleBasedKernelRegistryWriter
from ..writer.types import KernelRegistrySaveMetadata


@dataclass
class PickleBasedKernelRegistryRecoveryArgs:
    ipc_base_path: Path
    var_base_path: Path
    local_instance_id: str


class PickleBasedKernelRegistryRecovery:
    def __init__(self, args: PickleBasedKernelRegistryRecoveryArgs) -> None:
        registry_file_name = f"kernel_registry.{args.local_instance_id}.dat"
        legacy_registry_file_path = args.ipc_base_path / registry_file_name
        last_registry_file_path = args.var_base_path / registry_file_name

        self._loader = PickleBasedKernelRegistryLoader(
            last_registry_file_path, legacy_registry_file_path
        )
        self._writer = PickleBasedKernelRegistryWriter(last_registry_file_path)

    async def save_kernel_registry(
        self, registry: KernelRegistry, metadata: KernelRegistrySaveMetadata
    ) -> None:
        await self._writer.save_kernel_registry(registry, metadata)

    async def load_kernel_registry(self) -> KernelRegistry:
        return await self._loader.load_kernel_registry()
