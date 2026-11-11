from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.permission import RelationSpecMismatch
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationCreator, RelationPurger

from .base import RelationLinkResult, RelationPair, RelationUnlinkResult


@dataclass(frozen=True)
class UpdateRelationAction[
    TScope: EntityIdentifier,
    TTarget: EntityIdentifier,
    TRow: Base,
](BaseRelationAction):
    """Unlink ``purge_pairs`` and link ``create_pairs`` in one transaction.

    A pair named on both sides is refused. Every entity named is asked for UPDATE.
    """

    create_pairs: Sequence[RelationPair[TScope, TTarget]]
    creator: RelationCreator[TScope, TTarget, TRow]
    purge_pairs: Sequence[RelationPair[TScope, TTarget]]
    purger: RelationPurger[TScope, TTarget, TRow]

    def __post_init__(self) -> None:
        # mypy widens a mismatched TRow to Base, so the row table is checked here.
        if self.creator.row_class() is not self.purger.row_class():
            raise RelationSpecMismatch(
                f"creator writes {self.creator.row_class().__name__} but purger removes "
                f"{self.purger.row_class().__name__}"
            )
        if both := set(self.create_pairs) & set(self.purge_pairs):
            raise InvalidAPIParameters(f"Pairs named to both create and purge: {both}")

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_relation"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        """Every entity the run names, each once and in the order first named."""
        pairs = (*self.create_pairs, *self.purge_pairs)
        return list(dict.fromkeys(entity for pair in pairs for entity in (pair.scope, pair.target)))


@dataclass(frozen=True)
class UpdateRelationActionResult[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """What the run did to each pair the caller named, in the order named."""

    linked: Sequence[RelationLinkResult[TScope, TTarget]]
    unlinked: Sequence[RelationUnlinkResult[TScope, TTarget]]
