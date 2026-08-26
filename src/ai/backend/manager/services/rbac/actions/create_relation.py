"""Linking two entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationCreator
from ai.backend.manager.services.rbac.actions.base import BaseEntityRelationAction

__all__ = (
    "CreateRelationAction",
    "CreateRelationActionResult",
)


@dataclass(frozen=True)
class CreateRelationAction[TRow: Base](BaseEntityRelationAction):
    creator: RelationCreator[TRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_relation"


@dataclass(frozen=True)
class CreateRelationActionResult:
    """``created`` is false when the pair was already linked."""

    created: bool
