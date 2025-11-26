import logging
from abc import ABC, abstractmethod

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ....agent.kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryLoader(ABC):
    """
    Loader interface for loading KernelRegistry
    """

    @abstractmethod
    async def load_kernel_registry(self) -> dict[KernelId, AbstractKernel]:
        """
        Load the KernelRegistry from persistent storage.
        Raises:
            KernelRegistryNotFound
            KernelRegistryLoadError
        Returns: The loaded KernelRegistry.
        """
        pass
