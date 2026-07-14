"""Scope-action validators specific to app config fragment writes (BEP-1052)."""

from __future__ import annotations

from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.validator.scope import ScopeActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.permission import NotEnoughPermission

__all__ = ("PublicAppConfigFragmentWriteValidator",)


class PublicAppConfigFragmentWriteValidator(ScopeActionValidator):
    """Restrict writes to public (global-scoped) fragments to superadmins.

    A public fragment is global-scoped and has no RBAC scope element, so the generic
    scope-chain check cannot represent it. Public writes are therefore superadmin-only
    (BEP-1052). This guard runs ahead of ``ScopeActionRBACValidator`` and no-ops for
    ``user`` / ``domain`` scopes, leaving those to the scope-chain check.
    """

    _config_provider: ManagerConfigProvider

    def __init__(self, config_provider: ManagerConfigProvider) -> None:
        self._config_provider = config_provider

    @override
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return
        if action.scope_type() != ScopeType.GLOBAL:
            return
        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return
        raise NotEnoughPermission("Creating a public app config fragment requires superadmin")
