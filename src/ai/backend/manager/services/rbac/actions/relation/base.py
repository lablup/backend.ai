from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, ScopeRef, ScopeType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction

__all__ = (
    "BaseEntityRelationAction",
    "RelationLinkResult",
    "RelationPair",
    "RelationSwitchResult",
    "RelationUnlinkResult",
)


@dataclass(frozen=True)
class RelationPair[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """The two entities one relation row stands between."""

    scope: TScope
    target: TTarget


@dataclass(frozen=True)
class RelationLinkResult[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """Whether the pair was linked by this run; a pair already linked answers False."""

    pair: RelationPair[TScope, TTarget]
    linked: bool


@dataclass(frozen=True)
class RelationUnlinkResult[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """Whether the pair was linked before this run; unlinking one that was not is
    silent."""

    pair: RelationPair[TScope, TTarget]
    unlinked: bool


@dataclass(frozen=True)
class RelationSwitchResult[TScope: EntityIdentifier, TTarget: EntityIdentifier]:
    """Whether the pair stood the other way before this run; switching one that was
    already this way is silent."""

    pair: RelationPair[TScope, TTarget]
    switched: bool


@dataclass(frozen=True)
class BaseEntityRelationAction[TScope: EntityIdentifier, TTarget: EntityIdentifier](
    BaseRelationAction
):
    """Base for the relations of one kind, named by the pairs they stand between.

    Every entity named is asked for the operation's permission: a row is about its pair,
    so reaching one side is not enough to put them in a relation, and a run covering
    several pairs is permitted only where every one of them is.
    """

    pairs: Sequence[RelationPair[TScope, TTarget]]

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        """Every entity the run names, each once and in the order first named."""
        seen: dict[tuple[ScopeType, EntityIdentifier], ScopeRef] = {}
        for pair in self.pairs:
            for entity in (pair.scope, pair.target):
                scope_type = ScopeType(entity.entity_type())
                seen.setdefault(
                    (scope_type, entity), ScopeRef(scope_type=scope_type, scope_id=entity)
                )
        return list(seen.values())
