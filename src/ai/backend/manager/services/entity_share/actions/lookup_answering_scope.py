"""Resolve which scope answers a share before the answer is checked against it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType, EntityShareID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.entity_share.lookups import EntityShareAnsweringScopeLookup
from ai.backend.manager.models.entity_share.row import EntityShareRow

__all__ = (
    "EntityShareAndCallerKey",
    "LookupEntityShareAnsweringScopeAction",
)


@dataclass(frozen=True)
class EntityShareAndCallerKey(LookupKey):
    """The share being answered and the person answering it."""

    share_id: EntityShareID
    caller_user_id: UserID

    @override
    def kind(self) -> str:
        return "share_id_and_caller"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"share_id": str(self.share_id), "caller_user_id": str(self.caller_user_id)}


@dataclass(frozen=True)
class LookupEntityShareAnsweringScopeAction(
    LookupEntityOpsAction[EntityShareRow, EntityIdentifier]
):
    """Resolve a share into the scope that answers it when this caller answers."""

    share_id: EntityShareID
    caller_user_id: UserID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityShareEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_entity_share_answering_scope"

    @override
    def lookup_key(self) -> EntityShareAndCallerKey:
        return EntityShareAndCallerKey(share_id=self.share_id, caller_user_id=self.caller_user_id)

    @override
    def to_lookup(self) -> EntityShareAnsweringScopeLookup:
        return EntityShareAnsweringScopeLookup(
            share_id=self.share_id, caller_user_id=self.caller_user_id
        )
