from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from ai.backend.logging.structured import StructuredLogger

from .abc import AbstractKernelRegistryWriter

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel


log = StructuredLogger(logging.getLogger(__spec__.name))


class NoopKernelRegistryWriter(AbstractKernelRegistryWriter):
    def __init__(self) -> None:
        pass

    @override
    async def save_kernel(self, kernel: AbstractKernel) -> None:
        log.debug("kernel recovery data save skipped by noop writer")
        return
