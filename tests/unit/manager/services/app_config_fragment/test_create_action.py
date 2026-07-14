"""Unit tests for CreateAppConfigFragmentAction's RBAC target resolution.

``target_element()`` decides the scope the RBAC scope validator authorizes a fragment
create against (BEP-1052): a user/domain fragment targets its USER/DOMAIN scope, while a
public fragment is global-scoped (no RBAC scope element) and thus superadmin-only.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)

type ActionFactory = Callable[[AppConfigScopeType, str], CreateAppConfigFragmentAction]


@pytest.fixture
def make_action() -> ActionFactory:
    """Builds a create action for a fragment at the given scope."""

    def _make(scope_type: AppConfigScopeType, scope_id: str) -> CreateAppConfigFragmentAction:
        return CreateAppConfigFragmentAction(
            creator_spec=AppConfigFragmentCreatorSpec(
                config_name="cfg",
                scope_type=scope_type,
                scope_id=scope_id,
                config={},
            )
        )

    return _make


class TestCreateTargetElement:
    def test_user_scope_targets_the_user_scope(self, make_action: ActionFactory) -> None:
        action = make_action(AppConfigScopeType.USER, "user-1")
        assert action.target_element() == RBACElementRef(RBACElementType.USER, "user-1")
        assert action.scope_type() == ScopeType.USER

    def test_domain_scope_targets_the_domain_scope(self, make_action: ActionFactory) -> None:
        action = make_action(AppConfigScopeType.DOMAIN, "default")
        assert action.target_element() == RBACElementRef(RBACElementType.DOMAIN, "default")
        assert action.scope_type() == ScopeType.DOMAIN

    def test_public_scope_has_no_scope_element(self, make_action: ActionFactory) -> None:
        action = make_action(AppConfigScopeType.PUBLIC, "")
        assert action.target_element() == RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")
        assert action.scope_type() == ScopeType.GLOBAL

    def test_target_element_uses_the_spec_scope_id(self, make_action: ActionFactory) -> None:
        action = make_action(AppConfigScopeType.USER, "victim-user")
        assert action.target_element() == RBACElementRef(RBACElementType.USER, "victim-user")
