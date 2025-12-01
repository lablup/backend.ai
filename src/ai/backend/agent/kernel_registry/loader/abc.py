import logging
from abc import ABC, abstractmethod

from ai.backend.logging import BraceStyleAdapter

from ..types import KernelRegistryType

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryLoader(ABC):
    """
    Loader interface for loading kernel registry.
    """

    @abstractmethod
    async def load_kernel_registry(self) -> KernelRegistryType:
        """
        Load the kernel registry from persistent storage.
        Returns: The kernel registry (mapping of KernelId to AbstractKernel).
        """
        pass
