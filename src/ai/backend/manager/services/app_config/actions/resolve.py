from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.types import AppConfigScopeArguments
from ai.backend.manager.services.app_config.actions.base import (
    AppConfigScopeAction,
    AppConfigScopeActionResult,
)


@dataclass
class ResolveAppConfigsAction(AppConfigScopeAction):
    """Resolve the merged ``AppConfig`` for each of ``config_names``.

    The only read shape: a single name is a one-element ``config_names``. Reads are the hot
    path and a client bootstraps several configs at once, so batching is the default rather
    than an optimization bolted beside a single-name variant.

    ``scope_arguments`` carries what the caller may name — the domain, and any scope
    dimension added later. Not the user: that half is injected from the session, so there is
    no field to put someone else's id in and a resolve can only ever be for the acting user.
    Leaving ``scope_arguments`` unset, or resolving with no session at all, is the anonymous
    pre-login read: only ``public``-scope fragments contribute.
    """

    config_names: list[str]
    scope_arguments: AppConfigScopeArguments | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        # The same session the service resolves against — an anonymous read has no user.
        user = current_user()
        return str(user.user_id) if user is not None else ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG, "")


@dataclass
class ResolveAppConfigsActionResult(AppConfigScopeActionResult):
    app_configs: list[AppConfigData]
    _user_id: UserID | None

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self._user_id) if self._user_id is not None else ""
