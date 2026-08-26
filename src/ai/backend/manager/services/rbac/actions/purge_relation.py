"""Removing the row that links two entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationPurger
from ai.backend.manager.services.rbac.actions.base import BaseEntityRelationAction

__all__ = (
    "PurgeRelationAction",
    "PurgeRelationActionResult",
)


@dataclass(frozen=True)
class PurgeRelationAction[TRow: Base](BaseEntityRelationAction):
    purger: RelationPurger[TRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_relation"


@dataclass(frozen=True)
class PurgeRelationActionResult:
    """``purged`` is false when the pair had no row to remove."""

    purged: bool
