"""Offer one existing entity to one email address."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import ENTITY_SHARE_ENTITY_TYPE
from ai.backend.common.data.entity.types import (
    EntityType,
    ScopeRef,
    ScopeType,
)
from ai.backend.manager.actions.v2.ops.base import CreateEntityOpsAction
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.creators import EntityShareCreator
from ai.backend.manager.models.entity_share.row import EntityShareRow

__all__ = ("CreateEntityShareAction",)


@dataclass
class CreateEntityShareAction(CreateEntityOpsAction[EntityShareRow, EntityShareData]):
    """Offer an entity, answered for by that entity.

    The scope is what is being offered rather than who it goes to: the invitee is an
    email that may belong to nobody yet, while the entity is what the caller has to be
    allowed to hand out.
    """

    creator: EntityShareCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ENTITY_SHARE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_entity_share"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        target = self.creator.target
        return (ScopeRef(scope_type=ScopeType(target.entity_type()), scope_id=target),)

    @override
    def to_creator(self) -> EntityShareCreator:
        return self.creator
