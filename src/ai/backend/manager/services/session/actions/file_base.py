from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class SessionFileAction(SessionAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_FILE
