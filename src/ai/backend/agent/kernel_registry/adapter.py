from __future__ import annotations

import logging
from dataclasses import dataclass

from ai.backend.logging import BraceStyleAdapter

from .exception import KernelRegistryNotFound
from .loader.abc import AbstractKernelRegistryLoader
from .writer.abc import AbstractKernelRegistryWriter
from .writer.types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class KernelRecoveryDataAdapterTarget:
    loader: AbstractKernelRegistryLoader
    writer: AbstractKernelRegistryWriter


class KernelRecoveryDataAdapter:
    """
    Adapts Docker kernel recovery data.
    1. Loads recovery data using the source loader.
    2. Loads recovery data using the target loader to ensure compatibility.
    3. Saves the recovery data using the target writer.
    """

    def __init__(
        self,
        source_loader: AbstractKernelRegistryLoader,
        targets: list[KernelRecoveryDataAdapterTarget],
    ) -> None:
        self._source_loader = source_loader
        self._targets = targets

    async def adapt_recovery_data(self) -> None:
        try:
            source_data = await self._source_loader.load_kernel_registry()
        except KernelRegistryNotFound:
            log.info("No source kernel registry found to adapt.")
            return
        for target in self._targets:
            data = await target.loader.load_kernel_registry()
            for kernel_id, kernel in source_data.items():
                if kernel_id not in data:
                    data[kernel_id] = kernel
            metadata = KernelRegistrySaveMetadata(force=True)
            await target.writer.save_kernel_registry(data, metadata)
