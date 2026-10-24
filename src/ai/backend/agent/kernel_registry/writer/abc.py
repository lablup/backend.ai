from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ai.backend.logging.structured import StructuredLogger

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = StructuredLogger(logging.getLogger(__spec__.name))


class AbstractKernelRegistryWriter(ABC):
    """
    Writer interface for saving kernel recovery data.
    """

    @abstractmethod
    async def save_kernel(self, kernel: AbstractKernel) -> None:
        """
        Save the recovery data of a single kernel to persistent storage.
        """
        pass
