import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ....agent.kernel import AbstractKernel
from .types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryWriter(ABC):
    """
    Writer interface for saving kernel registry
    """

    @abstractmethod
    async def save_kernel_registry(
        self, registry: Mapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        """
        Save the kernel registry to persistent storage.
        args:
            registry: The kernel registry to save.
            metadata: Additional metadata for saving.
        Returns: None
        """
        pass
