from __future__ import annotations

import logging
from typing import Self

from ai.backend.agent.kernel_registry.loader.noop import NoopKernelRegistryLoader
from ai.backend.agent.kernel_registry.writer.noop import NoopKernelRegistryWriter
from ai.backend.logging.structured import StructuredLogger

from .base_recovery import BaseKernelRegistryRecovery

log = StructuredLogger(logging.getLogger(__spec__.name))


class KubernetesKernelRegistryRecovery(BaseKernelRegistryRecovery):
    """
    The kubernetes agent has no persistent kernel registry yet, so it starts empty.
    """

    @classmethod
    def create(cls) -> Self:
        return cls(
            loader=NoopKernelRegistryLoader(),
            writers=[NoopKernelRegistryWriter()],
        )
