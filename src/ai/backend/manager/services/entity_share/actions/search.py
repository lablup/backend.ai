"""Listing invitations, from whichever side the reader stands on."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.entity_share.scopes import EntityShareTarget
from ai.backend.manager.models.entity_share.searchers import EntityShareSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = ("SearchEntitySharesAction",)


@dataclass
class SearchEntitySharesAction(OperationScopeOpsAction[EntityShareRow, EntityShareData]):
    """Page through the invitations the named sides reach, combined with OR.

    Every side is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    targets: Sequence[EntityShareTarget]
    searcher: EntityShareSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityShareEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_entity_shares"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> EntityShareSearcher:
        return self.searcher
