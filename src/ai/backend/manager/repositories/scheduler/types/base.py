"""Base types for scheduling operations."""

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.common.types import SlotName, SlotTypes


@dataclass
class SchedulingSpec:
    """Specification of requirements for scheduling operations."""

    known_slot_types: Mapping[SlotName, SlotTypes]
    max_container_count: int | None = None
