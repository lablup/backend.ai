import logging
from typing import override

from ai.backend.logging import BraceStyleAdapter

from .abc import AbstractKernelRegistryWriter
from .types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class NoopKernelRegistryWriter(AbstractKernelRegistryWriter[None]):
    def __init__(self) -> None:
        pass

    @override
    async def save_kernel_registry(
        self, registry: None, metadata: KernelRegistrySaveMetadata
    ) -> None:
        log.debug("NoopKernelRegistryWriter: skipping save_kernel_registry")
        return
