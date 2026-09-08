from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationPurger

from .base import BaseEntityRelationAction, RelationUnlinkResult


@dataclass(frozen=True)
class PurgeRelationAction[
    TScope: EntityIdentifier,
    TTarget: EntityIdentifier,
    TRow: Base,
](BaseEntityRelationAction[TScope, TTarget]):
    """Unlink every named pair.

    Which relation the run is about travels on the spec, so one wiring serves every
    kind; which entities it named is on the run's scopes.
    """

    purger: RelationPurger[TScope, TTarget, TRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_relation"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class PurgeRelationActionResult[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """What the run did to each pair the caller named, in the order named."""

    results: Sequence[RelationUnlinkResult[TScope, TTarget]]
