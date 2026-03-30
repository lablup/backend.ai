from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernelRegistryLoader(ABC):
    """
    Loader interface for loading kernel registry.
    """

    @abstractmethod
    async def load_kernel_registry(self) -> MutableMapping[KernelId, AbstractKernel]:
        """
        Load the kernel registry from persistent storage.
        Returns: The kernel registry (mapping of KernelId to AbstractKernel).
        """
        pass
