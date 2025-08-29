import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class GetInstalledStorageNamespacesAction(ArtifactAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_installed_storages"


@dataclass
class GetInstalledStorageNamspacesActionResult(BaseActionResult):
    result: dict[uuid.UUID, uuid.UUID]

    @override
    def entity_id(self) -> Optional[str]:
        return None
