from dataclasses import dataclass
from typing import Any, Optional

from ai.backend.manager.types import Creator


@dataclass
class ProjectResourcePolicyCreator(Creator):
    name: str
    max_vfolder_count: Optional[int]
    max_quota_scope_size: Optional[int]
    max_vfolder_size: Optional[int]
    max_network_count: Optional[int]

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_vfolder_count": self.max_vfolder_count,
            "max_quota_scope_size": self.max_quota_scope_size,
            # "max_vfolder_size": self.max_vfolder_size, # deprecated fields
            "max_network_count": self.max_network_count,
        }
