import logging
from abc import ABC, abstractmethod

from ai.backend.logging import BraceStyleAdapter

from ..types import KernelRegistryType
from .types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryWriter(ABC):
    """
    Writer interface for saving kernel registry.
    """

    @abstractmethod
    async def save_kernel_registry(
        self, data: KernelRegistryType, metadata: KernelRegistrySaveMetadata
    ) -> None:
        """
        Save the kernel registry to persistent storage.
        args:
            data: Kernel registry (mapping of KernelId to AbstractKernel) to be saved.
            metadata: Metadata for the save operation.
        Returns: None
        """
        pass
