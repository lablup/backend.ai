import logging
from abc import ABC, abstractmethod

from ai.backend.logging import BraceStyleAdapter

from ..kernel_registry import KernelRegistry
from .types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryRecovery(ABC):
    """
    Recovery interface for loading and saving KernelRegistry
    """

    @abstractmethod
    async def load_kernel_registry(self) -> KernelRegistry:
        """
        Load the KernelRegistry from persistent storage.
        Raises:
            KernelRegistryNotFound
            KernelRegistryLoadError
        Returns: The loaded KernelRegistry.
        """
        pass

    @abstractmethod
    async def save_kernel_registry(
        self, registry: KernelRegistry, metadata: KernelRegistrySaveMetadata
    ) -> None:
        """
        Save the KernelRegistry to persistent storage.
        args:
            registry: The KernelRegistry to save.
            metadata: Additional metadata for saving.
        Returns: None
        """
        pass
