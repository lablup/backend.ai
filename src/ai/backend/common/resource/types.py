from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Self

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
    total_capacity_slots: ResourceSlot  # available_slots

    def to_json(self) -> dict:
        return {
            "total_used_slots": self.total_used_slots.to_json(),
            "total_free_slots": self.total_free_slots.to_json(),
            "total_capacity_slots": self.total_capacity_slots.to_json(),
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            total_used_slots=ResourceSlot.from_json(data["total_used_slots"]),
            total_free_slots=ResourceSlot.from_json(data["total_free_slots"]),
            total_capacity_slots=ResourceSlot.from_json(data["total_capacity_slots"]),
        )
