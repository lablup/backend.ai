from __future__ import annotations

import logging
from collections.abc import MutableMapping

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.loader.abc import AbstractKernelRegistryLoader
from ai.backend.agent.kernel_registry.writer.abc import AbstractKernelRegistryWriter
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BaseKernelRegistryRecovery:
    def __init__(
        self,
        loader: AbstractKernelRegistryLoader,
        writers: list[AbstractKernelRegistryWriter],
    ) -> None:
        self._loader = loader
        self._writers = writers

    async def save_kernel_registry(
        self, data: MutableMapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        for writer in self._writers:
            await writer.save_kernel_registry(data, metadata)

    async def load_kernel_registry(self) -> MutableMapping[KernelId, AbstractKernel]:
        return await self._loader.load_kernel_registry()
