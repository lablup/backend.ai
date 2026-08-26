"""Switching a relation off, leaving the row behind."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationLifecycleUpdater
from ai.backend.manager.services.rbac.actions.base import BaseEntityRelationAction

__all__ = (
    "DeleteRelationAction",
    "DeleteRelationActionResult",
)


@dataclass(frozen=True)
class DeleteRelationAction[TRow: Base](BaseEntityRelationAction):
    updater: RelationLifecycleUpdater[TRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_relation"


@dataclass(frozen=True)
class DeleteRelationActionResult:
    """``deleted`` is false when the pair had no relation to switch off."""

    deleted: bool
