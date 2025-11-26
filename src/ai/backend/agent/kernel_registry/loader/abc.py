import logging
from abc import ABC, abstractmethod
from typing import Generic

from ai.backend.logging import BraceStyleAdapter

from ..types import TKernelRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryLoader(Generic[TKernelRegistry], ABC):
    """
    Loader interface for loading KernelRegistry
    """

    @abstractmethod
    async def load_kernel_registry(self) -> TKernelRegistry:
        """
        Load the KernelRegistry from persistent storage.
        Raises:
            KernelRegistryNotFound
            KernelRegistryLoadError
        Returns: The loaded KernelRegistry.
        """
        pass
