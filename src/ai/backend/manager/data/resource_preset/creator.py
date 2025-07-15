from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.types import Creator


@dataclass
class ResourcePresetCreator(Creator):
    """Creator for resource preset operations."""
    
    name: str
    resource_slots: ResourceSlot
    shared_memory: Optional[int] = None
    
    @override
    def fields_to_store(self) -> dict[str, Any]:
        to_store = {
            "name": self.name,
            "resource_slots": self.resource_slots,
        }
        if self.shared_memory is not None:
            to_store["shared_memory"] = self.shared_memory
        return to_store