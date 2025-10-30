import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ai.backend.logging import BraceStyleAdapter

from .kernel_registry import KernelRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


SAVE_COOL_DOWN_SECONDS = 60


@dataclass
class KernelRegistrySaveMetadata:
    force: bool


class AbstractKernelRegistryRecovery(ABC):
    @abstractmethod
    async def load_kernel_registry(self) -> Optional[KernelRegistry]:
        pass

    @abstractmethod
    async def save_kernel_registry(
        self, registry: KernelRegistry, metadata: KernelRegistrySaveMetadata
    ) -> None:
        pass
