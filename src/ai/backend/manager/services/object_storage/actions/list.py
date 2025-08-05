from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class ListObjectStorageAction(ObjectStorageAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


# TODO: Make this BatchActionResult
@dataclass
class ListObjectStorageActionResult(BaseActionResult):
    data: list[ObjectStorageData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
