import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.logging import BraceStyleAdapter

from .kernel_registry import KernelRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


SAVE_COOL_DOWN_SECONDS = 60


@dataclass
class KernelRegistrySaveMetadata:
    force: bool


class AbstractKernelRegistryRecovery(ABC):
    """
    Recovery interface for loading and saving KernelRegistry
    """

    @abstractmethod
    async def load_kernel_registry(self) -> KernelRegistry:
        """
        Load the KernelRegistry from persistent storage.
        Raise ai.backend.agent.exception.KernelRegistryNotFound if not found.
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
