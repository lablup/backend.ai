import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.types import Creator


class ProjectType(enum.StrEnum):
    GENERAL = "general"
    MODEL_STORE = "model-store"

    @classmethod
    def _missing_(cls, value: Any) -> "Optional[ProjectType]":
        assert isinstance(value, str)
        match value.upper():
            case "GENERAL":
                return cls.GENERAL
            case "MODEL_STORE" | "MODEL-STORE":
                return cls.MODEL_STORE
        return None


@dataclass
class ProjectData:
    """
    Represents project data.
    """

    id: uuid.UUID
    name: str
    type: ProjectType
    domain_name: str
    description: Optional[str]
    total_resource_slots: ResourceSlot
    created_at: datetime
    updated_at: datetime


@dataclass
class ProjectCreator(Creator):
    name: str
    domain_name: str
    resource_policy: str
    type: ProjectType = ProjectType.GENERAL
    description: Optional[str] = None
    is_active: bool = True
    total_resource_slots: Optional[ResourceSlot] = None
    allowed_vfolder_hosts: dict[str, str] = field(default_factory=dict)
    integration_id: Optional[str] = None
    container_registry: Optional[dict[str, str]] = None

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain_name": self.domain_name,
            "type": self.type,
            "description": self.description,
            "is_active": self.is_active,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "integration_id": self.integration_id,
            "resource_policy": self.resource_policy,
            "container_registry": self.container_registry,
        }
