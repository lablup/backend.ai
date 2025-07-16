from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ai.backend.common.types import BinarySize, ResourceSlot


@dataclass
class ResourcePresetData:
    id: UUID
    name: str
    resource_slots: ResourceSlot
    shared_memory: Optional[BinarySize]
    scaling_group_name: Optional[str]
