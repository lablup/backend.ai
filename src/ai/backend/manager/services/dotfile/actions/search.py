from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.dotfile.scopes import UserDotfileTarget
from ai.backend.manager.models.dotfile.searchers import DotfileSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass(frozen=True)
class SearchDotfilesAction(OperationScopeOpsAction[DotfileRow, DotfileData]):
    """Page through the dotfiles the named users own, OR'd across them."""

    user_ids: Sequence[UserID]
    searcher: DotfileSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return tuple(self.user_ids)

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return tuple(UserDotfileTarget(user_id) for user_id in self.user_ids)

    @override
    def to_searcher(self) -> DotfileSearcher:
        return self.searcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_dotfiles"
