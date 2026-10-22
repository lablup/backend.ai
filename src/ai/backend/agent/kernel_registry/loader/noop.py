import logging
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, override

from ai.backend.common.types import KernelId
from ai.backend.logging.structured import StructuredLogger

from .abc import AbstractKernelRegistryLoader

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = StructuredLogger(logging.getLogger(__spec__.name))


class NoopKernelRegistryLoader(AbstractKernelRegistryLoader):
    def __init__(self) -> None:
        pass

    @override
    async def load_kernel_registry(self) -> MutableMapping[KernelId, AbstractKernel]:
        log.debug("kernel registry load skipped by noop loader")
        return {}
