from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


@dataclass
class VFolderAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.VFOLDER
