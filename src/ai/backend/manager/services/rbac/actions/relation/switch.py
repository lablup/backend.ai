from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationLifecycleUpdater

from .base import BaseEntityRelationAction, RelationSwitchResult


@dataclass(frozen=True)
class DeleteRelationAction[
    TScope: EntityIdentifier,
    TTarget: EntityIdentifier,
    TRow: Base,
](BaseEntityRelationAction[TScope, TTarget]):
    """Switch every named pair off, leaving the row and what each side reads of the
    other in place."""

    updater: RelationLifecycleUpdater[TScope, TTarget, TRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_relation"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class DeleteRelationActionResult[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """What the run did to each pair the caller named, in the order named."""

    results: Sequence[RelationSwitchResult[TScope, TTarget]]


@dataclass(frozen=True)
class RestoreRelationAction[
    TScope: EntityIdentifier,
    TTarget: EntityIdentifier,
    TRow: Base,
](BaseEntityRelationAction[TScope, TTarget]):
    """Switch every named pair back on."""

    updater: RelationLifecycleUpdater[TScope, TTarget, TRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_relation"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.RESTORE


@dataclass(frozen=True)
class RestoreRelationActionResult[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """What the run did to each pair the caller named, in the order named."""

    results: Sequence[RelationSwitchResult[TScope, TTarget]]
