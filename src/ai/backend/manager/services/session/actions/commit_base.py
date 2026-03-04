from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.services.session.base import SessionSingleEntityAction


@dataclass
class SessionCommitAction(SessionSingleEntityAction):
    """Base class for session commit actions that operate on a specific session.
    Inherits session_id requirement from SessionSingleEntityAction."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_COMMIT
