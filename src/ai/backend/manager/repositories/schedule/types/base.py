"""Base types for scheduling operations."""

from dataclasses import dataclass
from typing import Mapping, Optional

from ai.backend.common.types import SlotName, SlotTypes


@dataclass
class SchedulingSpec:
    """Specification of requirements for scheduling operations."""

    known_slot_types: Mapping[SlotName, SlotTypes]
    max_container_count: Optional[int] = None
