from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.services.session.base import SessionSingleEntityAction


@dataclass
class SessionAppServiceAction(SessionSingleEntityAction):
    """Base class for session app service actions that operate on a specific session.
    Inherits session_id requirement from SessionSingleEntityAction."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_APP_SERVICE
