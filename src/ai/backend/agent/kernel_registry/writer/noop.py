import logging
from collections.abc import Mapping
from typing import override

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ....agent.kernel import AbstractKernel
from .abc import AbstractKernelRegistryWriter
from .types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class NoopKernelRegistryWriter(AbstractKernelRegistryWriter):
    def __init__(self) -> None:
        pass

    @override
    async def save_kernel_registry(
        self, registry: Mapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        log.debug("NoopKernelRegistryWriter: skipping save_kernel_registry")
        return
