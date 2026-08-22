from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_ENTITY_TYPE
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.app_config.types import AppConfigData, AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.searchers import (
    RankedAppConfigFragmentSearcher,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.repositories.app_config_fragment.types import (
    PublicAppConfigFragmentOperationScope,
    VisibleAppConfigFragmentOperationScope,
)


@dataclass
class SearchAppConfigsAction(
    OperationScopeOpsAction[AppConfigFragmentRow, AppConfigFragmentData],
):
    """The merged ``AppConfig`` for each of ``config_names``, within one user's scope.

    Neither the user nor the domain is caller-supplied -- the adapter fills both from
    the session, so a read is only ever for the acting user.
    """

    config_names: list[str]
    user_id: UserID
    domain_id: DomainID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_app_configs"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (
            VisibleAppConfigFragmentOperationScope(user_id=self.user_id, domain_id=self.domain_id),
        )

    @override
    def to_searcher(self) -> Searcher[AppConfigFragmentRow, AppConfigFragmentData]:
        return RankedAppConfigFragmentSearcher(
            pagination=NoPagination(),
            conditions=[AppConfigFragmentConditions.by_config_names(self.config_names)],
        )


@dataclass
class AnonymousSearchAppConfigsAction(
    OperationScopeOpsAction[AppConfigFragmentRow, AppConfigFragmentData],
):
    """The merged ``AppConfig`` a caller sees before signing in.

    Names no principal, which is what limits the merge to the published fragments.
    It therefore names no RBAC scope either.
    """

    config_names: list[str]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "anonymous_search_app_configs"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return ()

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (PublicAppConfigFragmentOperationScope(),)

    @override
    def to_searcher(self) -> Searcher[AppConfigFragmentRow, AppConfigFragmentData]:
        return RankedAppConfigFragmentSearcher(
            pagination=NoPagination(),
            conditions=[AppConfigFragmentConditions.by_config_names(self.config_names)],
        )


@dataclass
class SearchAppConfigsActionResult(BaseScopeActionResult):
    """The merges asked for. Names no entity: a merge is a value, not a row."""

    app_configs: list[AppConfigData]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
