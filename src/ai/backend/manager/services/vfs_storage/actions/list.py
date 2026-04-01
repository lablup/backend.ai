from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class ListVFSStorageAction(VFSStorageAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListVFSStorageActionResult(BaseActionResult):
    data: list[VFSStorageData]

    @override
    def entity_id(self) -> str | None:
        return None
