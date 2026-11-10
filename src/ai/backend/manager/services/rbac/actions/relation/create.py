from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationCreator

from .base import BaseEntityRelationAction, RelationLinkResult


@dataclass(frozen=True)
class CreateRelationAction[
    TScope: EntityIdentifier,
    TTarget: EntityIdentifier,
    TRow: Base,
](BaseEntityRelationAction[TScope, TTarget]):
    """Link every named pair.

    Which relation the run is about travels on the spec, so one wiring serves every
    kind; which entities it named is on the run's scopes.
    """

    creator: RelationCreator[TScope, TTarget, TRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_relation"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class CreateRelationActionResult[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """What the run did to each pair the caller named, in the order named."""

    results: Sequence[RelationLinkResult[TScope, TTarget]]
