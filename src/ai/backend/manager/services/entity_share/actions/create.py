"""Offer one existing entity to one scope, or to an address with no account yet."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.creators import EntityShareCreator

__all__ = (
    "CreateEntityShareAction",
    "CreateEntityShareActionResult",
)


@dataclass
class CreateEntityShareAction(BaseScopeAction):
    """Offer an entity, answered for by that entity.

    The scope checked is what is being offered rather than who it goes to: the
    recipient may be a scope the caller cannot reach, or an address belonging to
    nobody yet, while the entity is what the caller has to be allowed to hand out.
    """

    creator: EntityShareCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityShareEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_entity_share"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        target = self.creator.target
        return (target,)


@dataclass
class CreateEntityShareActionResult(BaseScopeActionResult):
    """The offer that was written, or the one that already stood."""

    data: EntityShareData

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.data.id,)
