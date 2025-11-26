import logging
from abc import ABC, abstractmethod
from typing import Generic

from ai.backend.logging import BraceStyleAdapter

from ..types import TKernelRegistry
from .types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryWriter(Generic[TKernelRegistry], ABC):
    """
    Writer interface for saving KernelRegistry
    """

    @abstractmethod
    async def save_kernel_registry(
        self, registry: TKernelRegistry, metadata: KernelRegistrySaveMetadata
    ) -> None:
        """
        Save the KernelRegistry to persistent storage.
        args:
            registry: The KernelRegistry to save.
            metadata: Additional metadata for saving.
        Returns: None
        """
        pass
