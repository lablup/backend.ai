import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from ai.backend.common.types import AgentId, KernelId
from ai.backend.logging import BraceStyleAdapter

from ...kernel import AbstractKernel
from ..loader.abc import AbstractKernelRegistryLoader
from ..loader.pickle import PickleBasedKernelRegistryLoader
from ..types import KernelRegistryType
from ..writer.abc import AbstractKernelRegistryWriter
from ..writer.pickle import PickleBasedKernelRegistryWriter
from ..writer.types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class KernelRegistryRecoveryArgs:
    ipc_base_path: Path
    var_base_path: Path
    agent_id: AgentId
    local_instance_id: str


class KernelRegistryRecovery:
    def __init__(
        self,
        loaders: list[AbstractKernelRegistryLoader],
        writer: AbstractKernelRegistryWriter,
    ) -> None:
        self._loaders = loaders
        self._writer = writer

    @classmethod
    def create(cls, args: KernelRegistryRecoveryArgs) -> Self:
        registry_file_name = f"kernel_registry.{args.agent_id}.dat"
        fallback_registry_file_name = f"kernel_registry.{args.local_instance_id}.dat"
        legacy_registry_file_path = args.ipc_base_path / registry_file_name
        fallback_registry_file_path = args.var_base_path / fallback_registry_file_name
        last_registry_file_path = args.var_base_path / registry_file_name

        return cls(
            loaders=[
                PickleBasedKernelRegistryLoader(
                    last_registry_file_path,
                    fallback_registry_file_path,
                    legacy_registry_file_path,
                )
            ],
            writer=PickleBasedKernelRegistryWriter(last_registry_file_path),
        )

    async def save_kernel_registry(
        self, data: KernelRegistryType, metadata: KernelRegistrySaveMetadata
    ) -> None:
        await self._writer.save_kernel_registry(data, metadata)

    async def load_kernel_registry(self) -> KernelRegistryType:
        result: dict[KernelId, AbstractKernel] = {}
        for loader in self._loaders:
            try:
                loaded = await loader.load_kernel_registry()
                result.update(loaded)
            except Exception as e:
                log.warning(
                    "Failed to load kernel registry using loader {}, skip (err: {})",
                    loader.__class__.__name__,
                    str(e),
                )
                continue
        return result
