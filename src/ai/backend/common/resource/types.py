from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.types import ResourceSlot


class AbstractResource(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the resource.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def setup(self) -> None:
        """
        Set up the resource.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def release(self) -> None:
        """
        Release the resource.
        """
        raise NotImplementedError("Subclasses must implement this method.")


@dataclass
class TotalResourceData:
    total_used_slots: ResourceSlot  # occupied_slots
    total_free_slots: ResourceSlot  # total - occupied_slots
    total_capable_slots: ResourceSlot  # available_slots
