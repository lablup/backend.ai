from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentScopeAction,
    AppConfigFragmentScopeActionResult,
)


@dataclass
class ScopedSearchAppConfigFragmentAction(AppConfigFragmentScopeAction):
    """Search the fragments written at one scope.

    Acts at the RBAC scope named by ``scope``, so the scope RBAC validator authorizes the
    read the same way it authorizes a write at that scope in
    :class:`CreateAppConfigFragmentAction`.
    """

    scope: AppConfigFragmentSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return self.scope.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self.scope.scope_type.to_rbac_scope_id(self.scope.scope_id)

    @override
    def target_element(self) -> RBACElementRef:
        """The element RBAC enters the permission chain at — the scope owner, not the fragment.

        A domain / user scope resolves from its owner element. ``public`` is global and owns
        no element, so it names the fragment element with an empty id, which only a
        superadmin passes.
        """
        owner_element = self.scope.scope_type.to_rbac_element_type()
        if owner_element is None:
            return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")
        return RBACElementRef(owner_element, str(self.scope.scope_id))


@dataclass
class ScopedSearchAppConfigFragmentActionResult(AppConfigFragmentScopeActionResult):
    #: The searched scope, carried only to report the RBAC scope — not part of the result data.
    _scope: AppConfigFragmentSearchScope
    data: list[AppConfigFragmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def scope_type(self) -> ScopeType:
        return self._scope.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self._scope.scope_type.to_rbac_scope_id(self._scope.scope_id)
