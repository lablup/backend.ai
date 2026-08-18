from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.session.lookups import SessionNameOfUserLookup
from ai.backend.manager.models.session.row import SessionRow


@dataclass(frozen=True)
class SessionNameOfUserKey(LookupKey):
    """The name a caller passes instead of the session's id, with the user it is under."""

    user_uuid: UUID
    name: str

    @override
    def kind(self) -> str:
        return "session_name_of_user"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"user_uuid": str(self.user_uuid), "name": self.name}


@dataclass
class LookupSessionAction(LookupEntityOpsAction[SessionRow, SessionData]):
    """Resolve a session's name within its owner into the session it names."""

    user_uuid: UUID
    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_session"

    @override
    def lookup_key(self) -> SessionNameOfUserKey:
        return SessionNameOfUserKey(user_uuid=self.user_uuid, name=self.name)

    @override
    def to_lookup(self) -> SessionNameOfUserLookup:
        return SessionNameOfUserLookup(user_uuid=self.user_uuid, name=self.name)
