"""Resolve which scope answers a share before the answer is checked against it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType, EntityShareID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.lookup.base import (
    BaseLookupAction,
    BaseLookupActionResult,
    LookupKey,
)

__all__ = (
    "EntityShareIDKey",
    "LookupEntityShareAnsweringScopeAction",
    "LookupEntityShareAnsweringScopeActionResult",
)


@dataclass(frozen=True)
class EntityShareIDKey(LookupKey):
    """The share whose answering scope is read."""

    share_id: EntityShareID

    @override
    def kind(self) -> str:
        return "share_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"share_id": str(self.share_id)}


@dataclass(frozen=True)
class LookupEntityShareAnsweringScopeAction(BaseLookupAction):
    """Resolve a share into the scope that answers it.

    Resolving costs READ on that scope, the user or the project the share names.
    """

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


@dataclass(frozen=True)
class LookupEntityShareAnsweringScopeActionResult(BaseLookupActionResult):
    answering_scope: EntityIdentifier

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.answering_scope
