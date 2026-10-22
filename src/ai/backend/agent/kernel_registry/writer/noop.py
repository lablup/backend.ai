import logging
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, override

from ai.backend.common.types import KernelId
from ai.backend.logging.structured import StructuredLogger

from .abc import AbstractKernelRegistryWriter
from .types import KernelRegistrySaveMetadata

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel


log = StructuredLogger(logging.getLogger(__spec__.name))


class NoopKernelRegistryWriter(AbstractKernelRegistryWriter):
    def __init__(self) -> None:
        pass

    @override
    async def save_kernel_registry(
        self, data: MutableMapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        log.debug("kernel registry save skipped by noop writer")
        return
