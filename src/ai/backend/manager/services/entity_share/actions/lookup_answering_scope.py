"""Resolve which scope answers a share before the answer is checked against it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType, EntityShareID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.entity_share.lookups import EntityShareAnsweringScopeLookup
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

__all__ = (
    "EntityShareIDKey",
    "LookupEntityShareAnsweringScopeAction",
)


@dataclass(frozen=True)
class EntityShareIDKey(LookupKey):
    """The share whose recipient is read."""

    share_id: EntityShareID

    @override
    def kind(self) -> str:
        return "share_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"share_id": str(self.share_id)}


@dataclass(frozen=True)
class LookupEntityShareAnsweringScopeAction(
    LookupEntityOpsAction[VirtualEntityRow, RuntimeEntityID]
):
    """Resolve a share into the scope that answers it."""

    share_id: EntityShareID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityShareEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_entity_share_answering_scope"

    @override
    def lookup_key(self) -> EntityShareIDKey:
        return EntityShareIDKey(share_id=self.share_id)

    @override
    def to_lookup(self) -> EntityShareAnsweringScopeLookup:
        return EntityShareAnsweringScopeLookup(share_id=self.share_id)
