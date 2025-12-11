from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from .types import KernelRegistrySaveMetadata

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryWriter(ABC):
    """
    Writer interface for saving kernel registry.
    """

    @abstractmethod
    async def save_kernel_registry(
        self, data: MutableMapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        """
        Save the kernel registry to persistent storage.
        args:
            data: Kernel registry (mapping of KernelId to AbstractKernel) to be saved.
            metadata: Metadata for the save operation.
        Returns: None
        """
        pass
