"""Switching a relation back on."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationLifecycleUpdater
from ai.backend.manager.services.rbac.actions.base import BaseEntityRelationAction

__all__ = (
    "RestoreRelationAction",
    "RestoreRelationActionResult",
)


@dataclass(frozen=True)
class RestoreRelationAction[TRow: Base](BaseEntityRelationAction):
    updater: RelationLifecycleUpdater[TRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.RESTORE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_relation"


@dataclass(frozen=True)
class RestoreRelationActionResult:
    """``restored`` is false when the pair had no relation to switch back on."""

    restored: bool
