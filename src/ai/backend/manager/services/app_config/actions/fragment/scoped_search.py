from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import (
    APP_CONFIG_FRAGMENT_ENTITY_TYPE,
    AppConfigScopeID,
)
from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    ScopeRef,
    ScopeType,
)
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.scopes import AppConfigFragmentOperationScope
from ai.backend.manager.models.app_config_fragment.searchers import (
    AppConfigFragmentSearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class ScopedSearchAppConfigFragmentAction(
    OperationScopeOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Search the fragments one owner holds; ``None`` reads the ``public`` ones.

    The public rows carry the values every caller already reads merged, including before
    signing in, so they are answered for by authentication alone.
    """

    owner: EntityIdentifier | None
    searcher: AppConfigFragmentSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_FRAGMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_app_config_fragments"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        owner = self.owner
        if owner is None:
            return ()
        return (ScopeRef(scope_type=ScopeType(owner.entity_type()), scope_id=owner),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        owner = self.owner
        return (
            AppConfigFragmentOperationScope(
                scope_type=AppConfigScopeType.of_owner(owner),
                scope_id=None if owner is None else AppConfigScopeID(owner),
            ),
        )

    @override
    def to_searcher(self) -> AppConfigFragmentSearcher:
        return self.searcher
