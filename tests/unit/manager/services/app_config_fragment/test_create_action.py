"""Unit tests for CreateAppConfigFragmentAction's RBAC target resolution.

``target_element()`` decides the scope the RBAC scope validator authorizes a fragment
create against (BEP-1052): a user/domain fragment targets its USER/DOMAIN scope, while a
public fragment is global-scoped (no RBAC scope element) and thus superadmin-only.
"""

from __future__ import annotations

from typing import Any

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)


def _action(scope_type: AppConfigScopeType, scope_id: str) -> CreateAppConfigFragmentAction:
    spec: AppConfigFragmentCreatorSpec = AppConfigFragmentCreatorSpec(
        config_name="cfg",
        scope_type=scope_type,
        scope_id=scope_id,
        config={},
    )
    return CreateAppConfigFragmentAction(creator_spec=spec)


class TestCreateTargetElement:
    def test_user_scope_targets_the_user_scope(self) -> None:
        action = _action(AppConfigScopeType.USER, "user-1")
        assert action.target_element() == RBACElementRef(RBACElementType.USER, "user-1")
        assert action.scope_type() == ScopeType.USER

    def test_domain_scope_targets_the_domain_scope(self) -> None:
        action = _action(AppConfigScopeType.DOMAIN, "default")
        assert action.target_element() == RBACElementRef(RBACElementType.DOMAIN, "default")
        assert action.scope_type() == ScopeType.DOMAIN

    def test_public_scope_has_no_scope_element(self) -> None:
        # A public fragment is global-scoped: its target carries the fragment element type
        # with an empty id, so the scope-chain check finds no scope and denies any
        # non-superadmin writer (public writes are superadmin-only).
        action = _action(AppConfigScopeType.PUBLIC, "")
        assert action.target_element() == RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")
        assert action.scope_type() == ScopeType.GLOBAL

    def test_target_element_uses_the_spec_scope_id(self) -> None:
        # Cross-user create: the target scope is the *supplied* user id, so RBAC checks the
        # writer's permission on that other user's scope (which they lack) — not their own.
        other: Any = "victim-user"
        action = _action(AppConfigScopeType.USER, other)
        assert action.target_element() == RBACElementRef(RBACElementType.USER, other)
