from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.scopes import UserBootstrapScriptTarget
from ai.backend.manager.models.bootstrap_script.searchers import BootstrapScriptSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass(frozen=True)
class SearchBootstrapScriptsAction(
    OperationScopeOpsAction[BootstrapScriptRow, BootstrapScriptData]
):
    """Page through the bootstrap scripts set on one user."""

    user_id: UserID
    searcher: BootstrapScriptSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.user_id,)

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (UserBootstrapScriptTarget(user_id=self.user_id),)

    @override
    def to_searcher(self) -> BootstrapScriptSearcher:
        return self.searcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_bootstrap_scripts"
